"""Wishlist service - business logic for wishlist management."""

from uuid import UUID

from common.logger import setup_logger
from common.models import GroupInfo, WishlistItemResponse
from common.s3_utils import s3_uri_to_presigned_url
from repositories.groups_repository import GroupsRepository
from repositories.wishlist_repository import WishlistRepository

from services.groups_service import BadRequestError, ForbiddenError, NotFoundError

logger = setup_logger(__name__)


class WishlistService:
    """Service for wishlist business logic."""

    def __init__(
        self,
        wishlist_repo: WishlistRepository | None = None,
        groups_repo: GroupsRepository | None = None,
    ):
        """Initialize service with repositories."""
        self.wishlist_repo = wishlist_repo or WishlistRepository()
        self.groups_repo = groups_repo or GroupsRepository()

    def get_user_wishlist(self, user_id: str) -> list[WishlistItemResponse]:
        """Get all wishlist items for a user."""
        items = self.wishlist_repo.get_user_wishlist_items(user_id)

        response_items = []
        for item in items:
            # Get groups for each item
            groups = self.wishlist_repo.get_item_groups(str(item.id))

            # Convert S3 URI to presigned URL
            photo_url = s3_uri_to_presigned_url(item.photo_url) if item.photo_url else None

            response_items.append(
                WishlistItemResponse(
                    id=item.id,
                    user_id=item.user_id,
                    name=item.name,
                    description=item.description,
                    url=item.url,
                    price=item.price,
                    photo_url=photo_url,
                    rank=item.rank,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    groups=[GroupInfo(id=g.id, name=g.name) for g in groups],
                )
            )

        return response_items

    def create_wishlist_item(
        self,
        user_id: str,
        name: str,
        description: str | None,
        url: str | None,
        price: float | None,
        photo_url: str | None,
        rank: int,
        group_ids: list[UUID],
    ) -> WishlistItemResponse:
        """Create a new wishlist item."""
        # Verify user is member of all specified groups
        for group_id in group_ids:
            membership = self.groups_repo.get_user_membership(user_id, str(group_id))
            if not membership:
                raise ForbiddenError(f"You are not a member of group {group_id}")

        # Create item
        item = self.wishlist_repo.create_item(user_id, name, description, url, price, photo_url, rank)

        if not item:
            raise BadRequestError("Failed to create wishlist item")

        # Assign to groups
        if group_ids:
            self.wishlist_repo.assign_item_to_groups(str(item.id), [str(gid) for gid in group_ids])

        # Get group names for response
        groups = self.wishlist_repo.get_item_groups(str(item.id))

        # Convert S3 URI to presigned URL
        photo_url_presigned = (
            s3_uri_to_presigned_url(item.photo_url) if item.photo_url else None
        )

        return WishlistItemResponse(
            id=item.id,
            user_id=item.user_id,
            name=item.name,
            description=item.description,
            url=item.url,
            price=item.price,
            photo_url=photo_url_presigned,
            rank=item.rank,
            created_at=item.created_at,
            updated_at=item.updated_at,
            groups=[GroupInfo(id=g.id, name=g.name) for g in groups],
        )

    def get_wishlist_item(self, user_id: str, item_id: str) -> WishlistItemResponse:
        """Get a single wishlist item."""
        item = self.wishlist_repo.get_item_by_id(item_id)

        if not item:
            raise NotFoundError("Wishlist item not found")

        # Check access: user owns item or is in a group with access
        is_owner = str(item.user_id) == user_id
        has_group_access = self.wishlist_repo.user_has_group_access_to_item(user_id, item_id)

        if not is_owner and not has_group_access:
            raise ForbiddenError("You do not have access to this wishlist item")

        # Get groups
        groups = self.wishlist_repo.get_item_groups(item_id)

        # Convert S3 URI to presigned URL
        photo_url = s3_uri_to_presigned_url(item.photo_url) if item.photo_url else None

        return WishlistItemResponse(
            id=item.id,
            user_id=item.user_id,
            name=item.name,
            description=item.description,
            url=item.url,
            price=item.price,
            photo_url=photo_url,
            rank=item.rank,
            created_at=item.created_at,
            updated_at=item.updated_at,
            groups=[GroupInfo(id=g.id, name=g.name) for g in groups],
        )

    def update_wishlist_item(
        self,
        user_id: str,
        item_id: str,
        name: str | None = None,
        description: str | None = None,
        url: str | None = None,
        price: float | None = None,
        photo_url: str | None = None,
        rank: int | None = None,
        group_ids: list[UUID] | None = None,
    ) -> WishlistItemResponse:
        """Update a wishlist item (owner only)."""
        # Check ownership
        item = self.wishlist_repo.get_item_by_id(item_id)
        if not item or str(item.user_id) != user_id:
            raise ForbiddenError("You can only update your own wishlist items")

        # Update item fields
        updated_item = self.wishlist_repo.update_item(
            item_id, name, description, url, price, photo_url, rank
        )

        if not updated_item:
            raise NotFoundError("Wishlist item not found")

        # Update group assignments if provided
        if group_ids is not None:
            # Verify user is member of all new groups
            for group_id in group_ids:
                membership = self.groups_repo.get_user_membership(user_id, str(group_id))
                if not membership:
                    raise ForbiddenError(f"You are not a member of group {group_id}")

            self.wishlist_repo.assign_item_to_groups(item_id, [str(gid) for gid in group_ids])

        # Get groups for response
        groups = self.wishlist_repo.get_item_groups(item_id)

        # Convert S3 URI to presigned URL
        photo_url_presigned = (
            s3_uri_to_presigned_url(updated_item.photo_url) if updated_item.photo_url else None
        )

        return WishlistItemResponse(
            id=updated_item.id,
            user_id=updated_item.user_id,
            name=updated_item.name,
            description=updated_item.description,
            url=updated_item.url,
            price=updated_item.price,
            photo_url=photo_url_presigned,
            rank=updated_item.rank,
            created_at=updated_item.created_at,
            updated_at=updated_item.updated_at,
            groups=[GroupInfo(id=g.id, name=g.name) for g in groups],
        )

    def reorder_items(self, user_id: str, items: list[dict]) -> None:
        """Reorder wishlist items by updating rank values."""
        if not items:
            raise BadRequestError("No items provided")

        for item_data in items:
            item_id = item_data.get("id")
            rank = item_data.get("rank")

            if not item_id or rank is None:
                continue

            # Verify ownership
            item = self.wishlist_repo.get_item_by_id(str(item_id))
            if not item or str(item.user_id) != user_id:
                raise ForbiddenError(f"You do not own item {item_id}")

            # Update rank
            self.wishlist_repo.update_item_rank(str(item_id), rank)

    def delete_wishlist_item(self, user_id: str, item_id: str) -> None:
        """Delete a wishlist item (owner only)."""
        # Check ownership
        item = self.wishlist_repo.get_item_by_id(item_id)
        if not item or str(item.user_id) != user_id:
            raise ForbiddenError("You can only delete your own wishlist items")

        # Delete item
        rows_deleted = self.wishlist_repo.delete_item(item_id)

        if rows_deleted == 0:
            raise NotFoundError("Wishlist item not found")
