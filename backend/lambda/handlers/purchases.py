"""Purchase management Lambda handler."""

from typing import Any

from common.auth import require_auth
from common.db import execute_delete, execute_insert, execute_query
from common.models import PurchaseCreate, PurchaseResponse
from common.responses import conflict, created, error, forbidden, no_content, not_found
from common.validators import get_path_parameter, validate_request_body


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle /purchases/* endpoints."""
    http_method = event["httpMethod"]
    path = event["path"]

    # Require authentication
    user, auth_error = require_auth(event)
    if not user:
        return auth_error

    user_id = str(user.sub)

    # Route to appropriate function
    if http_method == "POST" and path == "/purchases":
        return claim_item(event, user_id)
    elif http_method == "DELETE" and path.startswith("/purchases/"):
        # Path format: /purchases/{itemId}/{groupId}
        path_parts = path.split("/")
        if len(path_parts) >= 4:
            item_id = path_parts[2]
            group_id = path_parts[3]
            return unclaim_item(user_id, item_id, group_id)
        return error("Invalid path format", 400)

    return error("Not Found", 404)


def claim_item(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Claim (purchase) a wishlist item."""
    # Validate request body
    purchase_data, validation_error = validate_request_body(event, PurchaseCreate)
    if validation_error:
        return validation_error

    item_id = str(purchase_data.item_id)
    group_id = str(purchase_data.group_id)

    # Check if item exists
    item_query = """
        SELECT user_id FROM wishlist_items WHERE id = %s
    """
    item = execute_query(item_query, (item_id,), fetch_one=True)

    if not item:
        return not_found("Wishlist item not found")

    # Prevent users from claiming their own items
    if str(item["user_id"]) == user_id:
        return forbidden("You cannot purchase your own wishlist items")

    # Verify user is member of the group
    membership_query = """
        SELECT 1 FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """
    is_member = execute_query(membership_query, (user_id, group_id), fetch_one=True)

    if not is_member:
        return forbidden("You are not a member of this group")

    # Verify item is assigned to this group
    assignment_query = """
        SELECT 1 FROM item_group_assignments
        WHERE item_id = %s AND group_id = %s
    """
    is_assigned = execute_query(assignment_query, (item_id, group_id), fetch_one=True)

    if not is_assigned:
        return forbidden("This item is not shared with this group")

    # Check if item is already purchased in this group
    existing_query = """
        SELECT purchased_by FROM purchases
        WHERE item_id = %s AND group_id = %s
    """
    existing = execute_query(existing_query, (item_id, group_id), fetch_one=True)

    if existing:
        if str(existing["purchased_by"]) == user_id:
            return conflict("You have already claimed this item")
        return conflict("This item has already been claimed by another member")

    # Create purchase record
    purchase_query = """
        INSERT INTO purchases (item_id, purchased_by, group_id)
        VALUES (%s, %s, %s)
        RETURNING id, item_id, purchased_by, group_id, purchased_at
    """

    result = execute_insert(purchase_query, (item_id, user_id, group_id))

    if not result:
        return error("Failed to claim item", 500)

    return created(PurchaseResponse(**result))


def unclaim_item(user_id: str, item_id: str, group_id: str) -> dict[str, Any]:
    """Unclaim (un-purchase) a wishlist item."""
    # Check if purchase exists and user is the one who claimed it
    purchase_query = """
        SELECT purchased_by FROM purchases
        WHERE item_id = %s AND group_id = %s
    """

    purchase = execute_query(purchase_query, (item_id, group_id), fetch_one=True)

    if not purchase:
        return not_found("Purchase record not found")

    if str(purchase["purchased_by"]) != user_id:
        return forbidden("You can only unclaim items you have claimed")

    # Delete purchase record
    delete_query = """
        DELETE FROM purchases
        WHERE item_id = %s AND group_id = %s AND purchased_by = %s
    """

    rows_deleted = execute_delete(delete_query, (item_id, group_id, user_id))

    if rows_deleted == 0:
        return not_found("Purchase record not found")

    return no_content()
