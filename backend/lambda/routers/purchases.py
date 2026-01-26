"""Purchase management router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from common.db import execute_delete, execute_insert, execute_query
from common.models import AuthenticatedUser, PurchaseCreate, PurchaseResponse
from dependencies.auth import get_current_user

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PurchaseResponse)
async def claim_item(
    purchase_data: PurchaseCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Claim (purchase) a wishlist item."""
    user_id = str(current_user.sub)
    item_id = str(purchase_data.item_id)
    group_id = str(purchase_data.group_id)

    # Check if item exists
    item_query = """
        SELECT user_id FROM wishlist_items WHERE id = %s
    """
    item = execute_query(item_query, (item_id,), fetch_one=True)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )

    # Prevent users from claiming their own items
    if str(item["user_id"]) == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot purchase your own wishlist items",
        )

    # Verify user is member of the group
    membership_query = """
        SELECT 1 FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """
    is_member = execute_query(membership_query, (user_id, group_id), fetch_one=True)

    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )

    # Verify item is assigned to this group
    assignment_query = """
        SELECT 1 FROM item_group_assignments
        WHERE item_id = %s AND group_id = %s
    """
    is_assigned = execute_query(assignment_query, (item_id, group_id), fetch_one=True)

    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This item is not shared with this group",
        )

    # Check if item is already purchased in this group
    existing_query = """
        SELECT purchased_by FROM purchases
        WHERE item_id = %s AND group_id = %s
    """
    existing = execute_query(existing_query, (item_id, group_id), fetch_one=True)

    if existing:
        if str(existing["purchased_by"]) == user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already claimed this item",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This item has already been claimed by another member",
        )

    # Create purchase record
    purchase_query = """
        INSERT INTO purchases (item_id, purchased_by, group_id)
        VALUES (%s, %s, %s)
        RETURNING id, item_id, purchased_by, group_id, purchased_at
    """

    result = execute_insert(purchase_query, (item_id, user_id, group_id))

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to claim item",
        )

    return PurchaseResponse(**result)


@router.delete("/{item_id}/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unclaim_item(
    item_id: UUID,
    group_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Unclaim (un-purchase) a wishlist item."""
    user_id = str(current_user.sub)

    # Check if purchase exists and user is the one who claimed it
    purchase_query = """
        SELECT purchased_by FROM purchases
        WHERE item_id = %s AND group_id = %s
    """

    purchase = execute_query(purchase_query, (str(item_id), str(group_id)), fetch_one=True)

    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase record not found",
        )

    if str(purchase["purchased_by"]) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unclaim items you have claimed",
        )

    # Delete purchase record
    delete_query = """
        DELETE FROM purchases
        WHERE item_id = %s AND group_id = %s AND purchased_by = %s
    """

    rows_deleted = execute_delete(delete_query, (str(item_id), str(group_id), user_id))

    if rows_deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Purchase record not found",
        )
