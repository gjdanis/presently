"""Groups management FastAPI router."""

from fastapi import APIRouter, Depends, HTTPException, status, Response

from common.db import execute_delete, execute_insert, execute_query, execute_update
from common.logger import setup_logger
from common.models import (
    AuthenticatedUser,
    GroupBasicInfo,
    GroupCreate,
    GroupDetailResponse,
    GroupMemberResponse,
    GroupResponse,
    GroupsListResponse,
    GroupUpdate,
    WishlistItemInGroup,
    WishlistUserGroup,
)
from common.s3_utils import s3_uri_to_presigned_url
from dependencies.auth import get_current_user

logger = setup_logger(__name__)

router = APIRouter()


@router.get("", response_model=GroupsListResponse)
async def get_groups(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GroupsListResponse:
    """Get all groups for the authenticated user."""
    user_id = str(current_user.sub)

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

    return GroupsListResponse(groups=groups)


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GroupResponse:
    """Create a new group."""
    user_id = str(current_user.sub)

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group",
        )

    group_id = group_result["id"]

    # Add creator as admin member
    membership_query = """
        INSERT INTO group_memberships (user_id, group_id, role)
        VALUES (%s, %s, 'admin')
    """

    execute_update(membership_query, (user_id, group_id))

    # Return group with role
    response_data = {**group_result, "role": "admin", "member_count": 1}
    return GroupResponse(**response_data)


@router.get("/{group_id}", response_model=GroupDetailResponse)
async def get_group_detail(
    group_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GroupDetailResponse:
    """Get detailed group information including members and wishlists."""
    user_id = str(current_user.sub)

    # Check if user is a member
    membership_query = """
        SELECT role FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """

    membership = execute_query(membership_query, (user_id, group_id), fetch_one=True)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )

    # Get group details
    group_query = """
        SELECT id, name, description, created_at, updated_at
        FROM groups
        WHERE id = %s
    """

    group = execute_query(group_query, (group_id,), fetch_one=True)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

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
    wishlists_by_user: dict[str, list[dict]] = {}

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

        # Convert S3 URI to presigned URL if photo_url exists
        item_data["photo_url"] = s3_uri_to_presigned_url(item["photo_url"]) if item.get("photo_url") else None

        wishlists_by_user[owner_id].append(item_data)

    # Format wishlists response
    wishlists = [
        WishlistUserGroup(
            userId=str(member.user_id),
            userName=member.name,
            items=[WishlistItemInGroup(**item) for item in wishlists_by_user.get(str(member.user_id), [])],
        )
        for member in members
    ]

    return GroupDetailResponse(
        group=GroupBasicInfo(**group),
        members=members,
        wishlists=wishlists
    )


@router.put("/{group_id}")
async def update_group(
    group_id: str,
    update_data: GroupUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict:
    """Update group details (admin only)."""
    user_id = str(current_user.sub)

    # Check if user is admin
    if not _is_group_admin(user_id, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can update group details",
        )

    # Build dynamic UPDATE query
    updates = []
    params: list = []

    if update_data.name is not None:
        updates.append("name = %s")
        params.append(update_data.name)

    if update_data.description is not None:
        updates.append("description = %s")
        params.append(update_data.description)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    params.append(group_id)

    query = f"""
        UPDATE groups
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, name, description, created_at, updated_at
    """

    result = execute_query(query, tuple(params), fetch_one=True)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return result


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    """Delete a group (admin only)."""
    user_id = str(current_user.sub)

    # Check if user is admin
    if not _is_group_admin(user_id, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can delete groups",
        )

    query = "DELETE FROM groups WHERE id = %s"
    rows_deleted = execute_delete(query, (group_id,))

    if rows_deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{group_id}/members/{user_id_to_remove}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str,
    user_id_to_remove: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
    """Remove a member from a group (admin only)."""
    user_id = str(current_user.sub)

    # Check if current user is admin
    if not _is_group_admin(user_id, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can remove members",
        )

    # Prevent removing yourself if you're the only admin
    admin_count_query = """
        SELECT COUNT(*) as count FROM group_memberships
        WHERE group_id = %s AND role = 'admin'
    """
    admin_count_result = execute_query(admin_count_query, (group_id,), fetch_one=True)

    if admin_count_result and admin_count_result["count"] == 1 and user_id == user_id_to_remove:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the only admin from the group",
        )

    # Remove member
    delete_query = """
        DELETE FROM group_memberships
        WHERE group_id = %s AND user_id = %s
    """
    rows_deleted = execute_delete(delete_query, (group_id, user_id_to_remove))

    if rows_deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this group",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _is_group_admin(user_id: str, group_id: str) -> bool:
    """Check if user is an admin of the group."""
    query = """
        SELECT role FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """
    result = execute_query(query, (user_id, group_id), fetch_one=True)
    return result is not None and result["role"] == "admin"
