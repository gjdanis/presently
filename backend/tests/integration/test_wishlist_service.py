"""Integration tests for WishlistService."""

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from services.groups_service import ForbiddenError, NotFoundError
from services.wishlist_service import WishlistService


@pytest.fixture
def wishlist_service() -> WishlistService:
    """Create a WishlistService instance."""
    return WishlistService()


@pytest.fixture
def sample_wishlist_item(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]
) -> dict[str, Any]:
    """Create a sample wishlist item."""
    cursor = clean_db.cursor()

    cursor.execute(
        """
        INSERT INTO wishlist_items (user_id, name, description, url, price, rank)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, user_id, name, description, url, price, rank, created_at, updated_at
        """,
        (sample_profile["id"], "Test Item", "A test item", "https://example.com", 99.99, 0)
    )

    item_result = cursor.fetchone()

    # Assign to group
    cursor.execute(
        "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
        (str(item_result[0]), sample_group["id"])
    )

    clean_db.commit()
    cursor.close()

    return {
        "id": str(item_result[0]),
        "user_id": str(item_result[1]),
        "name": item_result[2],
        "description": item_result[3],
        "url": item_result[4],
        "price": float(item_result[5]),
        "rank": item_result[6],
        "created_at": item_result[7],
        "updated_at": item_result[8],
    }


def test_get_user_wishlist_empty(
    clean_db: Any, sample_profile: dict[str, Any], wishlist_service: WishlistService
):
    """Test getting wishlist for user with no items."""
    items = wishlist_service.get_user_wishlist(sample_profile["id"])
    assert items == []


def test_get_user_wishlist_with_items(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    sample_wishlist_item: dict[str, Any],
    wishlist_service: WishlistService,
):
    """Test getting wishlist for user with items."""
    items = wishlist_service.get_user_wishlist(sample_profile["id"])
    assert len(items) == 1
    assert items[0].id == UUID(sample_wishlist_item["id"])
    assert items[0].name == sample_wishlist_item["name"]
    assert len(items[0].groups) == 1
    assert items[0].groups[0].id == UUID(sample_group["id"])


def test_create_wishlist_item(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], wishlist_service: WishlistService
):
    """Test creating a wishlist item."""
    item = wishlist_service.create_wishlist_item(
        user_id=sample_profile["id"],
        name="New Item",
        description="A new item",
        url="https://example.com/new",
        price=49.99,
        photo_url=None,
        rank=0,
        group_ids=[UUID(sample_group["id"])],
    )

    assert item.name == "New Item"
    assert item.description == "A new item"
    assert item.price == Decimal("49.99")
    assert len(item.groups) == 1


def test_create_wishlist_item_not_group_member(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], wishlist_service: WishlistService
):
    """Test creating item for group user is not a member of."""
    # Create another group
    cursor = clean_db.cursor()
    cursor.execute(
        "INSERT INTO groups (name, created_by) VALUES (%s, %s) RETURNING id",
        ("Other Group", sample_profile["id"])
    )
    other_group_id = str(cursor.fetchone()[0])
    clean_db.commit()
    cursor.close()

    with pytest.raises(ForbiddenError, match="not a member"):
        wishlist_service.create_wishlist_item(
            user_id=sample_profile["id"],
            name="Bad Item",
            description=None,
            url=None,
            price=None,
            photo_url=None,
            rank=0,
            group_ids=[UUID(other_group_id)],
        )


def test_get_wishlist_item_as_owner(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_wishlist_item: dict[str, Any],
    wishlist_service: WishlistService,
):
    """Test getting a wishlist item as the owner."""
    item = wishlist_service.get_wishlist_item(
        sample_profile["id"], sample_wishlist_item["id"]
    )

    assert item.id == UUID(sample_wishlist_item["id"])
    assert item.name == sample_wishlist_item["name"]


def test_get_wishlist_item_as_group_member(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    sample_wishlist_item: dict[str, Any],
    wishlist_service: WishlistService,
):
    """Test getting a wishlist item as a group member."""
    # Create another user in the group
    cursor = clean_db.cursor()
    member_id = str(uuid4())
    cursor.execute(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (member_id, "member@example.com", "Member")
    )
    cursor.execute(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (member_id, sample_group["id"], "member")
    )
    clean_db.commit()
    cursor.close()

    # Member should be able to see the item
    item = wishlist_service.get_wishlist_item(member_id, sample_wishlist_item["id"])
    assert item.id == UUID(sample_wishlist_item["id"])


def test_get_wishlist_item_no_access(
    clean_db: Any, sample_wishlist_item: dict[str, Any], wishlist_service: WishlistService
):
    """Test getting a wishlist item with no access."""
    stranger_id = str(uuid4())

    with pytest.raises(ForbiddenError, match="do not have access"):
        wishlist_service.get_wishlist_item(stranger_id, sample_wishlist_item["id"])


def test_update_wishlist_item(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_wishlist_item: dict[str, Any],
    wishlist_service: WishlistService,
):
    """Test updating a wishlist item."""
    updated = wishlist_service.update_wishlist_item(
        user_id=sample_profile["id"],
        item_id=sample_wishlist_item["id"],
        name="Updated Name",
        description="Updated description",
        url=None,
        price=199.99,
        photo_url=None,
        rank=None,
        group_ids=None,
    )

    assert updated.name == "Updated Name"
    assert updated.description == "Updated description"
    assert updated.price == Decimal("199.99")


def test_update_wishlist_item_not_owner(
    clean_db: Any, sample_wishlist_item: dict[str, Any], wishlist_service: WishlistService
):
    """Test updating a wishlist item as non-owner."""
    stranger_id = str(uuid4())

    with pytest.raises(ForbiddenError, match="only update your own"):
        wishlist_service.update_wishlist_item(
            user_id=stranger_id,
            item_id=sample_wishlist_item["id"],
            name="Hacked",
            description=None,
            url=None,
            price=None,
            photo_url=None,
            rank=None,
            group_ids=None,
        )


def test_delete_wishlist_item(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_wishlist_item: dict[str, Any],
    wishlist_service: WishlistService,
):
    """Test deleting a wishlist item."""
    wishlist_service.delete_wishlist_item(
        sample_profile["id"], sample_wishlist_item["id"]
    )

    # Verify item is deleted
    with pytest.raises(NotFoundError):
        wishlist_service.get_wishlist_item(
            sample_profile["id"], sample_wishlist_item["id"]
        )


def test_delete_wishlist_item_not_owner(
    clean_db: Any, sample_wishlist_item: dict[str, Any], wishlist_service: WishlistService
):
    """Test deleting a wishlist item as non-owner."""
    stranger_id = str(uuid4())

    with pytest.raises(ForbiddenError, match="only delete your own"):
        wishlist_service.delete_wishlist_item(stranger_id, sample_wishlist_item["id"])


def test_reorder_items(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], wishlist_service: WishlistService
):
    """Test reordering wishlist items."""
    # Create multiple items
    cursor = clean_db.cursor()
    item_ids = []

    for i in range(3):
        cursor.execute(
            """
            INSERT INTO wishlist_items (user_id, name, rank)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (sample_profile["id"], f"Item {i}", i)
        )
        item_id = str(cursor.fetchone()[0])
        item_ids.append(item_id)

        cursor.execute(
            "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
            (item_id, sample_group["id"])
        )

    clean_db.commit()
    cursor.close()

    # Reorder
    wishlist_service.reorder_items(
        sample_profile["id"],
        [
            {"id": item_ids[2], "rank": 0},
            {"id": item_ids[0], "rank": 1},
            {"id": item_ids[1], "rank": 2},
        ]
    )

    # Verify new order
    items = wishlist_service.get_user_wishlist(sample_profile["id"])
    assert items[0].name == "Item 2"
    assert items[1].name == "Item 0"
    assert items[2].name == "Item 1"
