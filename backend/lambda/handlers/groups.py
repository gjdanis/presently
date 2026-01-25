"""Groups management Lambda handler."""

from typing import Any
from uuid import UUID

from common.auth import require_auth
from common.db import execute_delete, execute_insert, execute_query, execute_update
from common.decorators import handle_cors
from common.models import GroupCreate, GroupMemberResponse, GroupResponse, GroupUpdate
from common.responses import conflict, created, error, forbidden, no_content, not_found, success
from common.validators import get_path_parameter, validate_request_body


@handle_cors("GET,POST,PUT,DELETE,OPTIONS")
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle /groups/* endpoints."""
    http_method = event["httpMethod"]
    path = event["path"]

    # Require authentication
    user, auth_error = require_auth(event)
    if not user:
        return auth_error

    user_id = str(user.sub)

    # Route to appropriate function
    if http_method == "GET" and path == "/groups":
        return get_groups(user_id)
    elif http_method == "POST" and path == "/groups":
        return create_group(event, user_id)
    elif http_method == "GET" and path.startswith("/groups/"):
        group_id, param_error = get_path_parameter(event, "groupId", is_uuid=True)
        if param_error:
            return param_error
        return get_group_detail(user_id, str(group_id))
    elif http_method == "PUT" and path.startswith("/groups/"):
        group_id, param_error = get_path_parameter(event, "groupId", is_uuid=True)
        if param_error:
            return param_error
        return update_group(event, user_id, str(group_id))
    elif http_method == "DELETE" and path.startswith("/groups/"):
        group_id, param_error = get_path_parameter(event, "groupId", is_uuid=True)
        if param_error:
            return param_error
        return delete_group(user_id, str(group_id))

    return error("Not Found", 404)


def get_groups(user_id: str) -> dict[str, Any]:
    """Get all groups for the authenticated user."""
    query = """
        SELECT g.id, g.name, g.description, gm.role, g.created_at, g.updated_at,
               COUNT(DISTINCT gm2.user_id) as member_count
        FROM groups g
        JOIN group_memberships gm ON g.id = gm.group_id
        LEFT JOIN group_memberships gm2 ON g.id = gm2.group_id
        WHERE gm.user_id = %s
        GROUP BY g.id, g.name, g.description, gm.role, g.created_at, g.updated_at
        ORDER BY g.created_at DESC
    """

    results = execute_query(query, (user_id,))
    groups = [GroupResponse(**row) for row in results]

    return success({"groups": groups})


def create_group(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Create a new group."""
    # Validate request body
    group_data, validation_error = validate_request_body(event, GroupCreate)
    if validation_error:
        return validation_error

    # Insert group
    group_query = """
        INSERT INTO groups (name, description, created_by)
        VALUES (%s, %s, %s)
        RETURNING id, name, description, created_at, updated_at
    """

    group_result = execute_insert(
        group_query, (group_data.name, group_data.description, user_id)
    )

    if not group_result:
        return error("Failed to create group", 500)

    group_id = group_result["id"]

    # Add creator as admin member
    membership_query = """
        INSERT INTO group_memberships (user_id, group_id, role)
        VALUES (%s, %s, 'admin')
    """

    from common.db import execute_update
    execute_update(membership_query, (user_id, group_id))

    # Return group with role
    response_data = {**group_result, "role": "admin", "member_count": 1}
    return created(GroupResponse(**response_data))


def get_group_detail(user_id: str, group_id: str) -> dict[str, Any]:
    """Get detailed group information including members and wishlists."""
    # Check if user is a member
    membership_query = """
        SELECT role FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """

    membership = execute_query(membership_query, (user_id, group_id), fetch_one=True)

    if not membership:
        return forbidden("You are not a member of this group")

    # Get group details
    group_query = """
        SELECT id, name, description, created_at, updated_at
        FROM groups
        WHERE id = %s
    """

    group = execute_query(group_query, (group_id,), fetch_one=True)

    if not group:
        return not_found("Group not found")

    # Get all members
    members_query = """
        SELECT gm.user_id, p.name, p.email, gm.role, gm.joined_at
        FROM group_memberships gm
        JOIN profiles p ON gm.user_id = p.id
        WHERE gm.group_id = %s
        ORDER BY gm.joined_at ASC
    """

    members_results = execute_query(members_query, (group_id,))
    members = [GroupMemberResponse(**row) for row in members_results]

    # Get wishlists for all members in this group
    wishlists_query = """
        SELECT wi.id, wi.user_id, wi.name, wi.description, wi.url,
               wi.price, wi.photo_url, wi.rank, wi.created_at, wi.updated_at,
               p.name as owner_name, p.email as owner_email,
               pur.purchased_by, pur.purchased_at
        FROM wishlist_items wi
        JOIN item_group_assignments iga ON wi.id = iga.item_id
        JOIN profiles p ON wi.user_id = p.id
        LEFT JOIN purchases pur ON wi.id = pur.item_id AND pur.group_id = %s
        WHERE iga.group_id = %s
        ORDER BY wi.user_id, wi.rank DESC, wi.created_at DESC
    """

    wishlist_results = execute_query(wishlists_query, (group_id, group_id))

    # Group wishlists by user
    wishlists_by_user: dict[str, list[dict[str, Any]]] = {}

    for item in wishlist_results:
        owner_id = str(item["user_id"])

        if owner_id not in wishlists_by_user:
            wishlists_by_user[owner_id] = []

        # Hide purchase info from item owner
        item_data = dict(item)
        if owner_id == user_id:
            item_data["is_purchased"] = None
            item_data["purchased_by"] = None
        else:
            item_data["is_purchased"] = item["purchased_by"] is not None
            item_data["purchased_by"] = item["purchased_by"]

        wishlists_by_user[owner_id].append(item_data)

    # Format wishlists response
    wishlists = [
        {
            "userId": str(member.user_id),
            "userName": member.name,
            "items": wishlists_by_user.get(str(member.user_id), []),
        }
        for member in members
    ]

    return success({"group": group, "members": members, "wishlists": wishlists})


def update_group(event: dict[str, Any], user_id: str, group_id: str) -> dict[str, Any]:
    """Update group details (admin only)."""
    # Check if user is admin
    if not _is_group_admin(user_id, group_id):
        return forbidden("Only group admins can update group details")

    # Validate request body
    update_data, validation_error = validate_request_body(event, GroupUpdate)
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

    if not updates:
        return error("No fields to update", 400)

    params.append(group_id)

    query = f"""
        UPDATE groups
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, name, description, created_at, updated_at
    """

    result = execute_query(query, tuple(params), fetch_one=True)

    if not result:
        return not_found("Group not found")

    return success(result)


def delete_group(user_id: str, group_id: str) -> dict[str, Any]:
    """Delete a group (admin only)."""
    # Check if user is admin
    if not _is_group_admin(user_id, group_id):
        return forbidden("Only group admins can delete groups")

    query = "DELETE FROM groups WHERE id = %s"
    rows_deleted = execute_delete(query, (group_id,))

    if rows_deleted == 0:
        return not_found("Group not found")

    return no_content()


def _is_group_admin(user_id: str, group_id: str) -> bool:
    """Check if user is an admin of the group."""
    query = """
        SELECT role FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """

    result = execute_query(query, (user_id, group_id), fetch_one=True)
    return result is not None and result["role"] == "admin"


def _is_group_member(user_id: str, group_id: str) -> bool:
    """Check if user is a member of the group."""
    query = """
        SELECT 1 FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """

    result = execute_query(query, (user_id, group_id), fetch_one=True)
    return result is not None
