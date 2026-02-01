"""Integration tests for PurchasesService."""

from typing import Any
from uuid import uuid4

import pytest
from services.groups_service import ForbiddenError, NotFoundError
from services.purchases_service import ConflictError, PurchasesService


@pytest.fixture
def purchases_service() -> PurchasesService:
    """Create a PurchasesService instance."""
    return PurchasesService()


@pytest.fixture
def second_profile(clean_db: Any) -> dict[str, Any]:
    """Create a second user profile for testing purchases."""
    user_id = uuid4()
    email = f"buyer-{uuid4()}@example.com"

    cursor = clean_db.cursor()
    cursor.execute(
        """
        INSERT INTO profiles (id, email, name)
        VALUES (%s, %s, %s)
        RETURNING id, email, name, created_at, updated_at
        """,
        (str(user_id), email, "Buyer User")
    )

    result = cursor.fetchone()
    clean_db.commit()
    cursor.close()

    return {
        "id": str(result[0]),
        "email": result[1],
        "name": result[2],
    }


@pytest.fixture
def wishlist_item_for_purchase(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], second_profile: dict[str, Any]
) -> dict[str, Any]:
    """Create a wishlist item that can be purchased."""
    cursor = clean_db.cursor()

    # Add second user to group
    cursor.execute(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (second_profile["id"], sample_group["id"], "member")
    )

    # Create wishlist item
    cursor.execute(
        """
        INSERT INTO wishlist_items (user_id, name, description, price, rank)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (sample_profile["id"], "Purchasable Item", "An item to purchase", 99.99, 0)
    )

    item_id = str(cursor.fetchone()[0])

    # Assign to group
    cursor.execute(
        "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
        (item_id, sample_group["id"])
    )

    clean_db.commit()
    cursor.close()

    return {
        "id": item_id,
        "owner_id": sample_profile["id"],
        "buyer_id": second_profile["id"],
        "group_id": sample_group["id"],
    }


def test_claim_item(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test claiming an item."""
    purchase = purchases_service.claim_item(
        user_id=wishlist_item_for_purchase["buyer_id"],
        item_id=wishlist_item_for_purchase["id"],
        group_id=wishlist_item_for_purchase["group_id"],
    )

    assert str(purchase.item_id) == wishlist_item_for_purchase["id"]
    assert str(purchase.purchased_by) == wishlist_item_for_purchase["buyer_id"]
    assert str(purchase.group_id) == wishlist_item_for_purchase["group_id"]
    assert purchase.id is not None


def test_claim_own_item(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test cannot claim own wishlist item."""
    with pytest.raises(ForbiddenError, match="cannot purchase your own"):
        purchases_service.claim_item(
            user_id=wishlist_item_for_purchase["owner_id"],
            item_id=wishlist_item_for_purchase["id"],
            group_id=wishlist_item_for_purchase["group_id"],
        )


def test_claim_nonexistent_item(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test claiming a non-existent item."""
    fake_item_id = str(uuid4())

    with pytest.raises(NotFoundError, match="not found"):
        purchases_service.claim_item(
            user_id=wishlist_item_for_purchase["buyer_id"],
            item_id=fake_item_id,
            group_id=wishlist_item_for_purchase["group_id"],
        )


def test_claim_item_not_group_member(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test claiming item when not a member of the group."""
    stranger_id = str(uuid4())

    # Create stranger profile
    cursor = clean_db.cursor()
    cursor.execute(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (stranger_id, "stranger@example.com", "Stranger")
    )
    clean_db.commit()
    cursor.close()

    with pytest.raises(ForbiddenError, match="not a member"):
        purchases_service.claim_item(
            user_id=stranger_id,
            item_id=wishlist_item_for_purchase["id"],
            group_id=wishlist_item_for_purchase["group_id"],
        )


def test_claim_item_not_in_group(
    clean_db: Any, sample_profile: dict[str, Any], second_profile: dict[str, Any], purchases_service: PurchasesService
):
    """Test claiming item that's not shared with the group."""
    # Create another group
    cursor = clean_db.cursor()
    cursor.execute(
        "INSERT INTO groups (name, created_by) VALUES (%s, %s) RETURNING id",
        ("Other Group", sample_profile["id"])
    )
    other_group_id = str(cursor.fetchone()[0])

    # Add second user to other group
    cursor.execute(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (second_profile["id"], other_group_id, "member")
    )

    # Create item not assigned to other group
    cursor.execute(
        """
        INSERT INTO wishlist_items (user_id, name, rank)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (sample_profile["id"], "Private Item", 0)
    )
    item_id = str(cursor.fetchone()[0])

    clean_db.commit()
    cursor.close()

    with pytest.raises(ForbiddenError, match="not shared with this group"):
        purchases_service.claim_item(
            user_id=second_profile["id"],
            item_id=item_id,
            group_id=other_group_id,
        )


def test_claim_already_claimed_by_self(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test claiming an item that user has already claimed."""
    # Claim once
    purchases_service.claim_item(
        user_id=wishlist_item_for_purchase["buyer_id"],
        item_id=wishlist_item_for_purchase["id"],
        group_id=wishlist_item_for_purchase["group_id"],
    )

    # Try to claim again
    with pytest.raises(ConflictError, match="already claimed"):
        purchases_service.claim_item(
            user_id=wishlist_item_for_purchase["buyer_id"],
            item_id=wishlist_item_for_purchase["id"],
            group_id=wishlist_item_for_purchase["group_id"],
        )


def test_claim_already_claimed_by_other(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test claiming an item that someone else has already claimed."""
    # First user claims
    purchases_service.claim_item(
        user_id=wishlist_item_for_purchase["buyer_id"],
        item_id=wishlist_item_for_purchase["id"],
        group_id=wishlist_item_for_purchase["group_id"],
    )

    # Create third user
    cursor = clean_db.cursor()
    third_user_id = str(uuid4())
    cursor.execute(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (third_user_id, "third@example.com", "Third User")
    )
    cursor.execute(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (third_user_id, wishlist_item_for_purchase["group_id"], "member")
    )
    clean_db.commit()
    cursor.close()

    # Third user tries to claim
    with pytest.raises(ConflictError, match="already been claimed by another"):
        purchases_service.claim_item(
            user_id=third_user_id,
            item_id=wishlist_item_for_purchase["id"],
            group_id=wishlist_item_for_purchase["group_id"],
        )


def test_unclaim_item(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test unclaiming an item."""
    # Claim first
    purchases_service.claim_item(
        user_id=wishlist_item_for_purchase["buyer_id"],
        item_id=wishlist_item_for_purchase["id"],
        group_id=wishlist_item_for_purchase["group_id"],
    )

    # Unclaim
    purchases_service.unclaim_item(
        user_id=wishlist_item_for_purchase["buyer_id"],
        item_id=wishlist_item_for_purchase["id"],
        group_id=wishlist_item_for_purchase["group_id"],
    )

    # Verify can claim again
    purchase = purchases_service.claim_item(
        user_id=wishlist_item_for_purchase["buyer_id"],
        item_id=wishlist_item_for_purchase["id"],
        group_id=wishlist_item_for_purchase["group_id"],
    )
    assert purchase.id is not None


def test_unclaim_not_claimed(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test unclaiming an item that hasn't been claimed."""
    with pytest.raises(NotFoundError, match="not found"):
        purchases_service.unclaim_item(
            user_id=wishlist_item_for_purchase["buyer_id"],
            item_id=wishlist_item_for_purchase["id"],
            group_id=wishlist_item_for_purchase["group_id"],
        )


def test_unclaim_someone_elses_claim(
    clean_db: Any, wishlist_item_for_purchase: dict[str, Any], purchases_service: PurchasesService
):
    """Test unclaiming an item claimed by someone else."""
    # First user claims
    purchases_service.claim_item(
        user_id=wishlist_item_for_purchase["buyer_id"],
        item_id=wishlist_item_for_purchase["id"],
        group_id=wishlist_item_for_purchase["group_id"],
    )

    # Create third user
    cursor = clean_db.cursor()
    third_user_id = str(uuid4())
    cursor.execute(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (third_user_id, "third@example.com", "Third User")
    )
    cursor.execute(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (third_user_id, wishlist_item_for_purchase["group_id"], "member")
    )
    clean_db.commit()
    cursor.close()

    # Third user tries to unclaim
    with pytest.raises(ForbiddenError, match="only unclaim items you have claimed"):
        purchases_service.unclaim_item(
            user_id=third_user_id,
            item_id=wishlist_item_for_purchase["id"],
            group_id=wishlist_item_for_purchase["group_id"],
        )
