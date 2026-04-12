"""Groups repository - handles all database operations for groups."""

from datetime import datetime
from uuid import UUID

from common.db import execute_delete, execute_insert, execute_query, execute_update
from common.logger import setup_logger
from pydantic import BaseModel

logger = setup_logger(__name__)


# Domain models (repository layer)
class GroupEntity(BaseModel):
    """Group entity from database."""

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GroupWithMembership(GroupEntity):
    """Group with user's membership info."""

    role: str
    member_count: int


class GroupMemberEntity(BaseModel):
    """Group member entity from database."""

    user_id: UUID
    name: str
    email: str
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class MembershipEntity(BaseModel):
    """Membership entity from database."""

    user_id: UUID
    group_id: UUID
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class WishlistItemEntity(BaseModel):
    """Wishlist item entity with purchase info."""

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
    owner_name: str
    owner_email: str
    purchased_by: UUID | None
    purchased_at: datetime | None

    class Config:
        from_attributes = True


class GroupsRepository:
    """Repository for groups data access."""

    def get_user_groups(self, user_id: str) -> list[GroupWithMembership]:
        """Get all groups for a user with membership info."""
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
        return [GroupWithMembership(**row) for row in results]

    def create_group(self, name: str, description: str | None, created_by: str) -> GroupEntity | None:
        """Create a new group."""
        query = """
            INSERT INTO groups (name, description, created_by)
            VALUES (%s, %s, %s)
            RETURNING id, name, description, created_at, updated_at
        """
        result = execute_insert(query, (name, description, created_by))
        return GroupEntity(**result) if result else None

    def get_group_by_id(self, group_id: str) -> GroupEntity | None:
        """Get group by ID."""
        query = """
            SELECT id, name, description, created_at, updated_at
            FROM groups
            WHERE id = %s
        """
        result = execute_query(query, (group_id,), fetch_one=True)
        return GroupEntity(**result) if result else None

    def update_group(
        self, group_id: str, name: str | None, description: str | None
    ) -> GroupEntity | None:
        """Update group details."""
        updates = []
        params: list = []

        if name is not None:
            updates.append("name = %s")
            params.append(name)

        if description is not None:
            updates.append("description = %s")
            params.append(description)

        if not updates:
            return None

        params.append(group_id)

        query = f"""
            UPDATE groups
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, name, description, created_at, updated_at
        """

        result = execute_query(query, tuple(params), fetch_one=True)
        return GroupEntity(**result) if result else None

    def delete_group(self, group_id: str) -> int:
        """Delete a group. Returns number of rows deleted."""
        query = "DELETE FROM groups WHERE id = %s"
        return execute_delete(query, (group_id,))

    def get_user_membership(self, user_id: str, group_id: str) -> MembershipEntity | None:
        """Get user's membership in a group."""
        query = """
            SELECT user_id, group_id, role, joined_at
            FROM group_memberships
            WHERE user_id = %s AND group_id = %s
        """
        result = execute_query(query, (user_id, group_id), fetch_one=True)
        return MembershipEntity(**result) if result else None

    def add_member(self, user_id: str, group_id: str, role: str = "member") -> None:
        """Add a member to a group."""
        query = """
            INSERT INTO group_memberships (user_id, group_id, role)
            VALUES (%s, %s, %s)
        """
        execute_update(query, (user_id, group_id, role))

    def remove_member(self, user_id: str, group_id: str) -> int:
        """Remove a member from a group. Returns number of rows deleted."""
        query = """
            DELETE FROM group_memberships
            WHERE group_id = %s AND user_id = %s
        """
        return execute_delete(query, (group_id, user_id))

    def get_group_members(self, group_id: str) -> list[GroupMemberEntity]:
        """Get all members of a group."""
        query = """
            SELECT gm.user_id, p.name, p.email, gm.role, gm.joined_at
            FROM group_memberships gm
            JOIN profiles p ON gm.user_id = p.id
            WHERE gm.group_id = %s
            ORDER BY gm.joined_at ASC
        """
        results = execute_query(query, (group_id,))
        return [GroupMemberEntity(**row) for row in results]

    def count_admins(self, group_id: str) -> int:
        """Count number of admins in a group."""
        query = """
            SELECT COUNT(*) as count FROM group_memberships
            WHERE group_id = %s AND role = 'admin'
        """
        result = execute_query(query, (group_id,), fetch_one=True)
        return result["count"] if result else 0

    def get_group_wishlist_items(self, group_id: str) -> list[WishlistItemEntity]:
        """Get all wishlist items shared with a group.

        Note: Shows purchased status if item is claimed in ANY group,
        not just the current group. This prevents duplicate purchases.
        """
        query = """
            SELECT wi.id, wi.user_id, wi.name, wi.description, wi.url,
                   wi.price, wi.photo_url, wi.rank, wi.received_at, wi.created_at, wi.updated_at,
                   p.name as owner_name, p.email as owner_email,
                   pur.purchased_by, pur.purchased_at
            FROM wishlist_items wi
            JOIN item_group_assignments iga ON wi.id = iga.item_id
            JOIN profiles p ON wi.user_id = p.id
            LEFT JOIN purchases pur ON wi.id = pur.item_id
            WHERE iga.group_id = %s AND wi.received_at IS NULL
            ORDER BY wi.user_id, wi.rank DESC, wi.created_at DESC
        """
        results = execute_query(query, (group_id,))
        return [WishlistItemEntity(**row) for row in results]
