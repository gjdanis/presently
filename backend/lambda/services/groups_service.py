"""Groups service - business logic for groups management."""

from common.logger import setup_logger
from common.models import (
    GroupBasicInfo,
    GroupDetailResponse,
    GroupMemberResponse,
    GroupResponse,
    WishlistItemInGroup,
    WishlistUserGroup,
)
from common.s3_utils import s3_uri_to_presigned_url
from fastapi import HTTPException, status
from repositories.groups_repository import GroupsRepository

logger = setup_logger(__name__)


class NotFoundError(Exception):
    """Resource not found error."""

    pass


class ForbiddenError(Exception):
    """Access forbidden error."""

    pass


class BadRequestError(Exception):
    """Bad request error."""

    pass


class GroupsService:
    """Service for groups business logic."""

    def __init__(self, repository: GroupsRepository | None = None):
        """Initialize service with repository."""
        self.repo = repository or GroupsRepository()

    def get_user_groups(self, user_id: str) -> list[GroupResponse]:
        """Get all groups for a user."""
        groups = self.repo.get_user_groups(user_id)
        return [
            GroupResponse(
                id=g.id,
                name=g.name,
                description=g.description,
                role=g.role,
                member_count=g.member_count,
                created_at=g.created_at,
                updated_at=g.updated_at,
            )
            for g in groups
        ]

    def create_group(self, user_id: str, name: str, description: str | None) -> GroupResponse:
        """Create a new group and add creator as admin."""
        # Create group
        group = self.repo.create_group(name, description, user_id)

        if not group:
            raise BadRequestError("Failed to create group")

        # Add creator as admin
        self.repo.add_member(user_id, str(group.id), role="admin")

        return GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            role="admin",
            member_count=1,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    def get_group_detail(self, user_id: str, group_id: str) -> GroupDetailResponse:
        """Get detailed group information with members and wishlists."""
        # Check membership
        membership = self.repo.get_user_membership(user_id, group_id)
        if not membership:
            raise ForbiddenError("You are not a member of this group")

        # Get group details
        group = self.repo.get_group_by_id(group_id)
        if not group:
            raise NotFoundError("Group not found")

        # Get members
        members = self.repo.get_group_members(group_id)

        # Get wishlist items
        wishlist_items = self.repo.get_group_wishlist_items(group_id)

        # Group items by user and apply privacy rules
        wishlists_by_user: dict[str, list[dict]] = {}

        for item in wishlist_items:
            owner_id = str(item.user_id)

            if owner_id not in wishlists_by_user:
                wishlists_by_user[owner_id] = []

            # Hide purchase info from item owner
            if owner_id == user_id:
                is_purchased = None
                purchased_by = None
            else:
                is_purchased = item.purchased_by is not None
                purchased_by = item.purchased_by

            # Convert S3 URI to presigned URL
            photo_url = s3_uri_to_presigned_url(item.photo_url) if item.photo_url else None

            wishlists_by_user[owner_id].append(
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "name": item.name,
                    "description": item.description,
                    "url": item.url,
                    "price": item.price,
                    "photo_url": photo_url,
                    "rank": item.rank,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "owner_name": item.owner_name,
                    "owner_email": item.owner_email,
                    "is_purchased": is_purchased,
                    "purchased_by": purchased_by,
                    "purchased_at": item.purchased_at,
                }
            )

        # Format wishlists response
        wishlists = [
            WishlistUserGroup(
                userId=str(member.user_id),
                userName=member.name,
                items=[
                    WishlistItemInGroup(**item)
                    for item in wishlists_by_user.get(str(member.user_id), [])
                ],
            )
            for member in members
        ]

        return GroupDetailResponse(
            group=GroupBasicInfo(
                id=group.id,
                name=group.name,
                description=group.description,
                created_at=group.created_at,
                updated_at=group.updated_at,
            ),
            members=[
                GroupMemberResponse(
                    user_id=m.user_id,
                    name=m.name,
                    email=m.email,
                    role=m.role,
                    joined_at=m.joined_at,
                )
                for m in members
            ],
            wishlists=wishlists,
        )

    def update_group(
        self, user_id: str, group_id: str, name: str | None, description: str | None
    ) -> GroupBasicInfo:
        """Update group details (admin only)."""
        # Check if user is admin
        if not self._is_admin(user_id, group_id):
            raise ForbiddenError("Only group admins can update group details")

        # Validate at least one field is provided
        if name is None and description is None:
            raise BadRequestError("No fields to update")

        # Update group
        group = self.repo.update_group(group_id, name, description)

        if not group:
            raise NotFoundError("Group not found")

        return GroupBasicInfo(
            id=group.id,
            name=group.name,
            description=group.description,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    def delete_group(self, user_id: str, group_id: str) -> None:
        """Delete a group (admin only)."""
        # Check if user is admin
        if not self._is_admin(user_id, group_id):
            raise ForbiddenError("Only group admins can delete groups")

        # Delete group
        rows_deleted = self.repo.delete_group(group_id)

        if rows_deleted == 0:
            raise NotFoundError("Group not found")

    def remove_member(self, user_id: str, group_id: str, user_id_to_remove: str) -> None:
        """Remove a member from a group (admin only)."""
        # Check if user is admin
        if not self._is_admin(user_id, group_id):
            raise ForbiddenError("Only group admins can remove members")

        # Prevent removing the only admin
        admin_count = self.repo.count_admins(group_id)
        if admin_count == 1 and user_id == user_id_to_remove:
            raise BadRequestError("Cannot remove the only admin from the group")

        # Remove member
        rows_deleted = self.repo.remove_member(user_id_to_remove, group_id)

        if rows_deleted == 0:
            raise NotFoundError("Member not found in this group")

    def _is_admin(self, user_id: str, group_id: str) -> bool:
        """Check if user is admin of the group."""
        membership = self.repo.get_user_membership(user_id, group_id)
        return membership is not None and membership.role == "admin"
