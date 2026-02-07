"""Purchases service - business logic for purchase/claim management."""

from common.logger import setup_logger
from common.models import PurchaseResponse
from repositories.groups_repository import GroupsRepository
from repositories.purchases_repository import PurchasesRepository
from repositories.wishlist_repository import WishlistRepository

from services.groups_service import BadRequestError, ForbiddenError, NotFoundError

logger = setup_logger(__name__)


class ConflictError(Exception):
    """Conflict error (resource already exists)."""

    pass


class PurchasesService:
    """Service for purchases business logic."""

    def __init__(
        self,
        purchases_repo: PurchasesRepository | None = None,
        wishlist_repo: WishlistRepository | None = None,
        groups_repo: GroupsRepository | None = None,
    ):
        """Initialize service with repositories."""
        self.purchases_repo = purchases_repo or PurchasesRepository()
        self.wishlist_repo = wishlist_repo or WishlistRepository()
        self.groups_repo = groups_repo or GroupsRepository()

    def claim_item(self, user_id: str, item_id: str, group_id: str) -> PurchaseResponse:
        """Claim (purchase) a wishlist item."""
        # Check if item exists
        item = self.wishlist_repo.get_item_by_id(item_id)
        if not item:
            raise NotFoundError("Wishlist item not found")

        # Prevent users from claiming their own items
        if str(item.user_id) == user_id:
            raise ForbiddenError("You cannot purchase your own wishlist items")

        # Verify user is member of the group
        membership = self.groups_repo.get_user_membership(user_id, group_id)
        if not membership:
            raise ForbiddenError("You are not a member of this group")

        # Verify item is assigned to this group
        if not self.purchases_repo.item_is_assigned_to_group(item_id, group_id):
            raise ForbiddenError("This item is not shared with this group")

        # Check if item is already claimed in ANY group (not just this group)
        # This prevents an item shared with multiple groups from being claimed multiple times
        if self.purchases_repo.item_is_claimed_anywhere(item_id):
            # Get the specific purchase to check if it's the same user
            existing_purchase = self.purchases_repo.get_purchase(item_id, group_id)
            if existing_purchase and str(existing_purchase.purchased_by) == user_id:
                raise ConflictError("You have already claimed this item")
            raise ConflictError("This item has already been claimed by another member")

        # Create purchase record
        purchase = self.purchases_repo.create_purchase(item_id, user_id, group_id)
        if not purchase:
            raise BadRequestError("Failed to claim item")

        return PurchaseResponse(
            id=purchase.id,
            item_id=purchase.item_id,
            purchased_by=purchase.purchased_by,
            group_id=purchase.group_id,
            purchased_at=purchase.purchased_at,
        )

    def unclaim_item(self, user_id: str, item_id: str, group_id: str) -> None:
        """Unclaim (un-purchase) a wishlist item.

        Note: Since items can be shared across multiple groups and purchases are global,
        we look up the purchase by item_id only (not by group_id).
        """
        # Check if purchase exists (regardless of which group it was claimed in)
        purchase = self.purchases_repo.get_purchase_by_item(item_id)

        if not purchase:
            raise NotFoundError("Purchase record not found")

        if str(purchase.purchased_by) != user_id:
            raise ForbiddenError("You can only unclaim items you have claimed")

        # Delete purchase record (by item, not by group)
        rows_deleted = self.purchases_repo.delete_purchase_by_item(item_id, user_id)

        if rows_deleted == 0:
            raise NotFoundError("Purchase record not found")
