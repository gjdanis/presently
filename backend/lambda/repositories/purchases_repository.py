"""Purchases repository - handles all database operations for purchases."""

from datetime import datetime
from uuid import UUID

from common.db import execute_delete, execute_insert, execute_query
from common.logger import setup_logger
from pydantic import BaseModel

logger = setup_logger(__name__)


# Domain models
class PurchaseEntity(BaseModel):
    """Purchase entity from database."""

    id: UUID
    item_id: UUID
    purchased_by: UUID
    group_id: UUID
    purchased_at: datetime

    class Config:
        from_attributes = True


class PurchasesRepository:
    """Repository for purchases data access."""

    def get_purchase(self, item_id: str, group_id: str) -> PurchaseEntity | None:
        """Get purchase record for an item in a group."""
        query = """
            SELECT id, item_id, purchased_by, group_id, purchased_at
            FROM purchases
            WHERE item_id = %s AND group_id = %s
        """
        result = execute_query(query, (item_id, group_id), fetch_one=True)
        return PurchaseEntity(**result) if result else None

    def create_purchase(
        self, item_id: str, purchased_by: str, group_id: str
    ) -> PurchaseEntity | None:
        """Create a purchase record."""
        query = """
            INSERT INTO purchases (item_id, purchased_by, group_id)
            VALUES (%s, %s, %s)
            RETURNING id, item_id, purchased_by, group_id, purchased_at
        """
        result = execute_insert(query, (item_id, purchased_by, group_id))
        return PurchaseEntity(**result) if result else None

    def delete_purchase(self, item_id: str, group_id: str, purchased_by: str) -> int:
        """Delete a purchase record. Returns number of rows deleted."""
        query = """
            DELETE FROM purchases
            WHERE item_id = %s AND group_id = %s AND purchased_by = %s
        """
        return execute_delete(query, (item_id, group_id, purchased_by))

    def item_is_assigned_to_group(self, item_id: str, group_id: str) -> bool:
        """Check if item is assigned to group."""
        query = """
            SELECT 1 FROM item_group_assignments
            WHERE item_id = %s AND group_id = %s
        """
        result = execute_query(query, (item_id, group_id), fetch_one=True)
        return result is not None
