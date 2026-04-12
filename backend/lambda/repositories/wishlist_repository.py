"""Wishlist repository - handles all database operations for wishlist items."""

from datetime import datetime
from uuid import UUID

from common.db import execute_delete, execute_insert, execute_query, execute_update
from common.logger import setup_logger
from pydantic import BaseModel

logger = setup_logger(__name__)

# Sentinel value to distinguish "not provided" from "explicitly None"
_NOT_PROVIDED = object()


# Domain models
class WishlistItemEntity(BaseModel):
    """Wishlist item entity from database."""

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    url: str | None
    price: float | None
    photo_url: str | None
    rank: int
    received_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GroupInfoEntity(BaseModel):
    """Group info entity."""

    id: UUID
    name: str

    class Config:
        from_attributes = True


class WishlistRepository:
    """Repository for wishlist items data access."""

    def get_user_wishlist_items(self, user_id: str) -> list[WishlistItemEntity]:
        """Get active (not received) wishlist items for a user."""
        query = """
            SELECT wi.id, wi.user_id, wi.name, wi.description, wi.url,
                   wi.price, wi.photo_url, wi.rank, wi.received_at, wi.created_at, wi.updated_at
            FROM wishlist_items wi
            WHERE wi.user_id = %s AND wi.received_at IS NULL
            ORDER BY wi.rank ASC, wi.created_at DESC
        """
        results = execute_query(query, (user_id,))
        return [WishlistItemEntity(**row) for row in results]

    def get_item_by_id(self, item_id: str) -> WishlistItemEntity | None:
        """Get wishlist item by ID."""
        query = """
            SELECT wi.id, wi.user_id, wi.name, wi.description, wi.url,
                   wi.price, wi.photo_url, wi.rank, wi.received_at, wi.created_at, wi.updated_at
            FROM wishlist_items wi
            WHERE wi.id = %s
        """
        result = execute_query(query, (item_id,), fetch_one=True)
        return WishlistItemEntity(**result) if result else None

    def toggle_item_received(self, item_id: str) -> WishlistItemEntity | None:
        """Toggle the received state of an item. Sets received_at if null, clears it if set."""
        query = """
            UPDATE wishlist_items
            SET received_at = CASE WHEN received_at IS NULL THEN NOW() ELSE NULL END
            WHERE id = %s
            RETURNING id, user_id, name, description, url, price, photo_url, rank,
                      received_at, created_at, updated_at
        """
        result = execute_query(query, (item_id,), fetch_one=True)
        return WishlistItemEntity(**result) if result else None

    def create_item(
        self,
        user_id: str,
        name: str,
        description: str | None,
        url: str | None,
        price: float | None,
        photo_url: str | None,
        rank: int,
    ) -> WishlistItemEntity | None:
        """Create a new wishlist item."""
        query = """
            INSERT INTO wishlist_items (user_id, name, description, url, price, photo_url, rank)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, user_id, name, description, url, price, photo_url, rank,
                      received_at, created_at, updated_at
        """
        result = execute_insert(query, (user_id, name, description, url, price, photo_url, rank))
        return WishlistItemEntity(**result) if result else None

    def update_item(
        self,
        item_id: str,
        name: str | None = None,
        description: str | None = None,
        url: str | None = None,
        price: float | None = None,
        photo_url: str | None | object = _NOT_PROVIDED,
        rank: int | None = None,
    ) -> WishlistItemEntity | None:
        """Update wishlist item fields. Use photo_url=None to clear the photo."""
        updates = []
        params: list = []

        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        if url is not None:
            updates.append("url = %s")
            params.append(url)
        if price is not None:
            updates.append("price = %s")
            params.append(price)
        if photo_url is not _NOT_PROVIDED:  # Allow explicit None to clear the photo
            updates.append("photo_url = %s")
            params.append(photo_url)
        if rank is not None:
            updates.append("rank = %s")
            params.append(rank)

        if not updates:
            return self.get_item_by_id(item_id)

        params.append(item_id)

        query = f"""
            UPDATE wishlist_items
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, user_id, name, description, url, price, photo_url, rank,
                      received_at, created_at, updated_at
        """
        result = execute_query(query, tuple(params), fetch_one=True)
        return WishlistItemEntity(**result) if result else None

    def delete_item(self, item_id: str) -> int:
        """Delete a wishlist item. Returns number of rows deleted."""
        query = "DELETE FROM wishlist_items WHERE id = %s"
        return execute_delete(query, (item_id,))

    def get_item_groups(self, item_id: str) -> list[GroupInfoEntity]:
        """Get groups assigned to an item."""
        query = """
            SELECT g.id, g.name
            FROM groups g
            JOIN item_group_assignments iga ON g.id = iga.group_id
            WHERE iga.item_id = %s
        """
        results = execute_query(query, (item_id,))
        return [GroupInfoEntity(**row) for row in results]

    def assign_item_to_groups(self, item_id: str, group_ids: list[str]) -> None:
        """Assign item to groups. Replaces existing assignments."""
        # Delete existing assignments
        execute_delete("DELETE FROM item_group_assignments WHERE item_id = %s", (item_id,))

        # Create new assignments
        for group_id in group_ids:
            query = "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)"
            execute_update(query, (item_id, group_id))

    def update_item_rank(self, item_id: str, rank: int) -> None:
        """Update item rank."""
        query = "UPDATE wishlist_items SET rank = %s WHERE id = %s"
        execute_update(query, (rank, item_id))

    def user_has_group_access_to_item(self, user_id: str, item_id: str) -> bool:
        """Check if user has access to item through group membership."""
        query = """
            SELECT 1 FROM item_group_assignments iga
            JOIN group_memberships gm ON iga.group_id = gm.group_id
            WHERE iga.item_id = %s AND gm.user_id = %s
        """
        result = execute_query(query, (item_id, user_id), fetch_one=True)
        return result is not None
