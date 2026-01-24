"""Wishlist management Lambda handler."""

import json
from typing import Any

from common.auth import require_auth
from common.db import execute_delete, execute_insert, execute_query, execute_update
from common.models import (
    GroupInfo,
    WishlistItemCreate,
    WishlistItemResponse,
    WishlistItemUpdate,
)
from common.responses import created, error, forbidden, no_content, not_found, success
from common.validators import get_path_parameter, validate_request_body


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle /wishlist/* endpoints."""
    http_method = event["httpMethod"]
    path = event["path"]

    # Require authentication
    user, auth_error = require_auth(event)
    if not user:
        return auth_error

    user_id = str(user.sub)

    # Route to appropriate function
    if http_method == "GET" and path == "/wishlist":
        return get_wishlist(user_id)
    elif http_method == "POST" and path == "/wishlist":
        return create_wishlist_item(event, user_id)
    elif http_method == "GET" and path.startswith("/wishlist/"):
        item_id, param_error = get_path_parameter(event, "itemId", is_uuid=True)
        if param_error:
            return param_error
        return get_wishlist_item(user_id, str(item_id))
    elif http_method == "PUT" and path.startswith("/wishlist/") and not path.endswith("/reorder"):
        item_id, param_error = get_path_parameter(event, "itemId", is_uuid=True)
        if param_error:
            return param_error
        return update_wishlist_item(event, user_id, str(item_id))
    elif http_method == "PUT" and path == "/wishlist/reorder":
        return reorder_wishlist_items(event, user_id)
    elif http_method == "DELETE" and path.startswith("/wishlist/"):
        item_id, param_error = get_path_parameter(event, "itemId", is_uuid=True)
        if param_error:
            return param_error
        return delete_wishlist_item(user_id, str(item_id))

    return error("Not Found", 404)


def get_wishlist(user_id: str) -> dict[str, Any]:
    """Get all wishlist items for the authenticated user."""
    query = """
        SELECT wi.id, wi.user_id, wi.name, wi.description, wi.url,
               wi.price, wi.photo_url, wi.rank, wi.created_at, wi.updated_at
        FROM wishlist_items wi
        WHERE wi.user_id = %s
        ORDER BY wi.rank DESC, wi.created_at DESC
    """

    results = execute_query(query, (user_id,))

    # Get groups for each item
    items = []
    for item in results:
        groups_query = """
            SELECT g.id, g.name
            FROM groups g
            JOIN item_group_assignments iga ON g.id = iga.group_id
            WHERE iga.item_id = %s
        """
        groups_results = execute_query(groups_query, (item["id"],))
        groups = [GroupInfo(**g) for g in groups_results]

        item_data = {**item, "groups": groups}
        items.append(WishlistItemResponse(**item_data))

    return success({"items": items})


def create_wishlist_item(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Create a new wishlist item."""
    # Validate request body
    item_data, validation_error = validate_request_body(event, WishlistItemCreate)
    if validation_error:
        return validation_error

    # Verify user is member of all specified groups
    for group_id in item_data.group_ids:
        if not _is_group_member(user_id, str(group_id)):
            return forbidden(f"You are not a member of group {group_id}")

    # Insert wishlist item
    item_query = """
        INSERT INTO wishlist_items (user_id, name, description, url, price, photo_url, rank)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, name, description, url, price, photo_url, rank, created_at, updated_at
    """

    item_result = execute_insert(
        item_query,
        (
            user_id,
            item_data.name,
            item_data.description,
            str(item_data.url) if item_data.url else None,
            item_data.price,
            str(item_data.photo_url) if item_data.photo_url else None,
            item_data.rank,
        ),
    )

    if not item_result:
        return error("Failed to create wishlist item", 500)

    item_id = item_result["id"]

    # Assign to groups
    from common.db import execute_update
    for group_id in item_data.group_ids:
        assignment_query = """
            INSERT INTO item_group_assignments (item_id, group_id)
            VALUES (%s, %s)
        """
        execute_update(assignment_query, (item_id, str(group_id)))

    # Get groups for response
    groups = [GroupInfo(id=gid, name="") for gid in item_data.group_ids]

    # Fetch actual group names
    if item_data.group_ids:
        groups_query = """
            SELECT id, name FROM groups WHERE id = ANY(%s::uuid[])
        """
        groups_results = execute_query(groups_query, (list(map(str, item_data.group_ids)),))
        groups = [GroupInfo(**g) for g in groups_results]

    response_data = {**item_result, "groups": groups}
    return created(WishlistItemResponse(**response_data))


def get_wishlist_item(user_id: str, item_id: str) -> dict[str, Any]:
    """Get a single wishlist item."""
    query = """
        SELECT wi.id, wi.user_id, wi.name, wi.description, wi.url,
               wi.price, wi.photo_url, wi.rank, wi.created_at, wi.updated_at
        FROM wishlist_items wi
        WHERE wi.id = %s
    """

    item = execute_query(query, (item_id,), fetch_one=True)

    if not item:
        return not_found("Wishlist item not found")

    # Check if user owns the item or is in a group with access
    if str(item["user_id"]) != user_id:
        access_query = """
            SELECT 1 FROM item_group_assignments iga
            JOIN group_memberships gm ON iga.group_id = gm.group_id
            WHERE iga.item_id = %s AND gm.user_id = %s
        """
        has_access = execute_query(access_query, (item_id, user_id), fetch_one=True)

        if not has_access:
            return forbidden("You do not have access to this wishlist item")

    # Get groups
    groups_query = """
        SELECT g.id, g.name
        FROM groups g
        JOIN item_group_assignments iga ON g.id = iga.group_id
        WHERE iga.item_id = %s
    """
    groups_results = execute_query(groups_query, (item_id,))
    groups = [GroupInfo(**g) for g in groups_results]

    response_data = {**item, "groups": groups}
    return success(WishlistItemResponse(**response_data))


def update_wishlist_item(event: dict[str, Any], user_id: str, item_id: str) -> dict[str, Any]:
    """Update a wishlist item (owner only)."""
    # Check ownership
    if not _is_item_owner(user_id, item_id):
        return forbidden("You can only update your own wishlist items")

    # Validate request body
    update_data, validation_error = validate_request_body(event, WishlistItemUpdate)
    if validation_error:
        return validation_error

    # Build dynamic UPDATE query
    updates = []
    params: list[Any] = []

    if update_data.name is not None:
        updates.append("name = %s")
        params.append(update_data.name)

    if update_data.description is not None:
        updates.append("description = %s")
        params.append(update_data.description)

    if update_data.url is not None:
        updates.append("url = %s")
        params.append(str(update_data.url) if update_data.url else None)

    if update_data.price is not None:
        updates.append("price = %s")
        params.append(update_data.price)

    if update_data.photo_url is not None:
        updates.append("photo_url = %s")
        params.append(str(update_data.photo_url) if update_data.photo_url else None)

    if update_data.rank is not None:
        updates.append("rank = %s")
        params.append(update_data.rank)

    # Update item if there are changes
    if updates:
        params.append(item_id)
        query = f"""
            UPDATE wishlist_items
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, user_id, name, description, url, price, photo_url, rank, created_at, updated_at
        """
        item = execute_query(query, tuple(params), fetch_one=True)
    else:
        # No item updates, just fetch current item
        item = execute_query(
            "SELECT * FROM wishlist_items WHERE id = %s", (item_id,), fetch_one=True
        )

    # Update group assignments if provided
    if update_data.group_ids is not None:
        # Verify user is member of all new groups
        for group_id in update_data.group_ids:
            if not _is_group_member(user_id, str(group_id)):
                return forbidden(f"You are not a member of group {group_id}")

        # Delete existing assignments
        execute_delete("DELETE FROM item_group_assignments WHERE item_id = %s", (item_id,))

        # Create new assignments
        for group_id in update_data.group_ids:
            execute_insert(
                "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
                (item_id, str(group_id)),
            )

    # Get groups for response
    groups_query = """
        SELECT g.id, g.name
        FROM groups g
        JOIN item_group_assignments iga ON g.id = iga.group_id
        WHERE iga.item_id = %s
    """
    groups_results = execute_query(groups_query, (item_id,))
    groups = [GroupInfo(**g) for g in groups_results]

    response_data = {**item, "groups": groups}
    return success(WishlistItemResponse(**response_data))


def reorder_wishlist_items(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Reorder wishlist items by updating rank values."""
    body = event.get("body")
    if not body:
        return error("Request body is required", 400)

    try:
        data = json.loads(body) if isinstance(body, str) else body
        items = data.get("items", [])

        if not items:
            return error("No items provided", 400)

        # Update rank for each item
        for item in items:
            item_id = item.get("id")
            rank = item.get("rank")

            if not item_id or rank is None:
                continue

            # Verify ownership
            if not _is_item_owner(user_id, str(item_id)):
                return forbidden(f"You do not own item {item_id}")

            # Update rank
            execute_update("UPDATE wishlist_items SET rank = %s WHERE id = %s", (rank, str(item_id)))

        return success({"success": True})

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return error(f"Invalid request: {str(e)}", 400)


def delete_wishlist_item(user_id: str, item_id: str) -> dict[str, Any]:
    """Delete a wishlist item (owner only)."""
    # Check ownership
    if not _is_item_owner(user_id, item_id):
        return forbidden("You can only delete your own wishlist items")

    query = "DELETE FROM wishlist_items WHERE id = %s"
    rows_deleted = execute_delete(query, (item_id,))

    if rows_deleted == 0:
        return not_found("Wishlist item not found")

    return no_content()


def _is_item_owner(user_id: str, item_id: str) -> bool:
    """Check if user owns the wishlist item."""
    query = "SELECT user_id FROM wishlist_items WHERE id = %s"
    result = execute_query(query, (item_id,), fetch_one=True)
    return result is not None and str(result["user_id"]) == user_id


def _is_group_member(user_id: str, group_id: str) -> bool:
    """Check if user is a member of the group."""
    query = """
        SELECT 1 FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """
    result = execute_query(query, (user_id, group_id), fetch_one=True)
    return result is not None
