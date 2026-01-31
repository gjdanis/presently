"""Wishlist management router."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from common.db import execute_delete, execute_insert, execute_query, execute_update
from common.models import (
    AuthenticatedUser,
    GroupInfo,
    WishlistItemCreate,
    WishlistItemResponse,
    WishlistItemUpdate,
)
from common.s3_utils import s3_uri_to_presigned_url
from dependencies.auth import get_current_user

router = APIRouter()


@router.get("", response_model=dict[str, list[WishlistItemResponse]])
async def get_wishlist(current_user: AuthenticatedUser = Depends(get_current_user)):
    """Get all wishlist items for the authenticated user."""
    user_id = str(current_user.sub)

    query = """
        SELECT wi.id, wi.user_id, wi.name, wi.description, wi.url,
               wi.price, wi.photo_url, wi.rank, wi.created_at, wi.updated_at
        FROM wishlist_items wi
        WHERE wi.user_id = %s
        ORDER BY wi.rank DESC, wi.created_at DESC
    """

    results = execute_query(query, (user_id,))

    # Get groups for each item and convert S3 URIs to presigned URLs
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

        # Convert S3 URI to presigned URL if photo_url exists
        photo_url = s3_uri_to_presigned_url(item["photo_url"]) if item.get("photo_url") else None

        item_data = {**item, "groups": groups, "photo_url": photo_url}
        items.append(WishlistItemResponse(**item_data))

    return {"items": items}


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WishlistItemResponse)
async def create_wishlist_item(
    item_data: WishlistItemCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a new wishlist item."""
    user_id = str(current_user.sub)

    # Verify user is member of all specified groups (if any)
    if item_data.group_ids:
        for group_id in item_data.group_ids:
            if not _is_group_member(user_id, str(group_id)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You are not a member of group {group_id}",
                )

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create wishlist item",
        )

    item_id = item_result["id"]

    # Assign to groups
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
    return WishlistItemResponse(**response_data)


@router.get("/{item_id}", response_model=WishlistItemResponse)
async def get_wishlist_item(
    item_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a single wishlist item."""
    user_id = str(current_user.sub)

    query = """
        SELECT wi.id, wi.user_id, wi.name, wi.description, wi.url,
               wi.price, wi.photo_url, wi.rank, wi.created_at, wi.updated_at
        FROM wishlist_items wi
        WHERE wi.id = %s
    """

    item = execute_query(query, (str(item_id),), fetch_one=True)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )

    # Check if user owns the item or is in a group with access
    if str(item["user_id"]) != user_id:
        access_query = """
            SELECT 1 FROM item_group_assignments iga
            JOIN group_memberships gm ON iga.group_id = gm.group_id
            WHERE iga.item_id = %s AND gm.user_id = %s
        """
        has_access = execute_query(access_query, (str(item_id), user_id), fetch_one=True)

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this wishlist item",
            )

    # Get groups
    groups_query = """
        SELECT g.id, g.name
        FROM groups g
        JOIN item_group_assignments iga ON g.id = iga.group_id
        WHERE iga.item_id = %s
    """
    groups_results = execute_query(groups_query, (str(item_id),))
    groups = [GroupInfo(**g) for g in groups_results]

    # Convert S3 URI to presigned URL if photo_url exists
    photo_url = s3_uri_to_presigned_url(item["photo_url"]) if item.get("photo_url") else None

    response_data = {**item, "groups": groups, "photo_url": photo_url}
    return WishlistItemResponse(**response_data)


@router.put("/{item_id}", response_model=WishlistItemResponse)
async def update_wishlist_item(
    item_id: UUID,
    update_data: WishlistItemUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Update a wishlist item (owner only)."""
    user_id = str(current_user.sub)

    # Check ownership
    if not _is_item_owner(user_id, str(item_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own wishlist items",
        )

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
        params.append(str(item_id))
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
            "SELECT * FROM wishlist_items WHERE id = %s", (str(item_id),), fetch_one=True
        )

    # Update group assignments if provided
    if update_data.group_ids is not None:
        # Verify user is member of all new groups
        for group_id in update_data.group_ids:
            if not _is_group_member(user_id, str(group_id)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You are not a member of group {group_id}",
                )

        # Delete existing assignments
        execute_delete("DELETE FROM item_group_assignments WHERE item_id = %s", (str(item_id),))

        # Create new assignments
        for group_id in update_data.group_ids:
            execute_query(
                "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
                (str(item_id), str(group_id)),
            )

    # Get groups for response
    groups_query = """
        SELECT g.id, g.name
        FROM groups g
        JOIN item_group_assignments iga ON g.id = iga.group_id
        WHERE iga.item_id = %s
    """
    groups_results = execute_query(groups_query, (str(item_id),))
    groups = [GroupInfo(**g) for g in groups_results]

    # Convert S3 URI to presigned URL if photo_url exists
    photo_url = s3_uri_to_presigned_url(item["photo_url"]) if item.get("photo_url") else None

    response_data = {**item, "groups": groups, "photo_url": photo_url}
    return WishlistItemResponse(**response_data)


@router.put("/reorder")
async def reorder_wishlist_items(
    reorder_data: dict[str, list[dict[str, Any]]],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Reorder wishlist items by updating rank values."""
    user_id = str(current_user.sub)

    items = reorder_data.get("items", [])

    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No items provided",
        )

    # Update rank for each item
    for item in items:
        item_id = item.get("id")
        rank = item.get("rank")

        if not item_id or rank is None:
            continue

        # Verify ownership
        if not _is_item_owner(user_id, str(item_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not own item {item_id}",
            )

        # Update rank
        execute_update("UPDATE wishlist_items SET rank = %s WHERE id = %s", (rank, str(item_id)))

    return {"success": True}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_item(
    item_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Delete a wishlist item (owner only)."""
    user_id = str(current_user.sub)

    # Check ownership
    if not _is_item_owner(user_id, str(item_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own wishlist items",
        )

    query = "DELETE FROM wishlist_items WHERE id = %s"
    rows_deleted = execute_delete(query, (str(item_id),))

    if rows_deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found",
        )


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
