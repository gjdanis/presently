"""Integration tests for wishlist endpoints with real database."""

import json
from typing import Any
from uuid import uuid4

from common.db import execute_query, execute_update


def test_create_wishlist_item(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test creating a wishlist item."""
    from handlers.wishlist import create_wishlist_item

    event = {
        "body": json.dumps({
            "name": "Test Item",
            "description": "A test wishlist item",
            "url": "https://example.com/product",
            "price": 99.99,
            "group_ids": [sample_group["id"]]
        })
    }

    response = create_wishlist_item(event, sample_profile["id"])

    assert response["statusCode"] == 201

    body = json.loads(response["body"])
    assert body["name"] == "Test Item"
    assert body["description"] == "A test wishlist item"
    assert float(body["price"]) == 99.99
    assert len(body["groups"]) == 1

    # Verify in database
    item = execute_query(
        "SELECT * FROM wishlist_items WHERE id = %s",
        (body["id"],),
        fetch_one=True
    )
    assert item is not None
    assert item["name"] == "Test Item"

    # Verify group assignment
    assignment = execute_query(
        "SELECT * FROM item_group_assignments WHERE item_id = %s AND group_id = %s",
        (body["id"], sample_group["id"]),
        fetch_one=True
    )
    assert assignment is not None


def test_get_user_wishlist(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test retrieving user's wishlist."""
    # Create an item
    execute_update(
        "INSERT INTO wishlist_items (user_id, name, description, rank) VALUES (%s, %s, %s, %s) RETURNING id",
        (sample_profile["id"], "Item 1", "Description 1", 0)
    )
    item_id = execute_query(
        "SELECT id FROM wishlist_items WHERE user_id = %s AND name = %s",
        (sample_profile["id"], "Item 1"),
        fetch_one=True
    )["id"]

    execute_update(
        "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
        (item_id, sample_group["id"])
    )

    from handlers.wishlist import get_wishlist

    response = get_wishlist(sample_profile["id"])

    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert "items" in body
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "Item 1"


def test_update_wishlist_item(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test updating a wishlist item."""
    # Create an item
    result = execute_query(
        "INSERT INTO wishlist_items (user_id, name, rank) VALUES (%s, %s, %s) RETURNING id",
        (sample_profile["id"], "Original Name", 0),
        fetch_one=True
    )
    item_id = str(result["id"])

    execute_update(
        "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
        (item_id, sample_group["id"])
    )

    from handlers.wishlist import update_wishlist_item

    event = {
        "body": json.dumps({
            "name": "Updated Name",
            "description": "New description"
        })
    }

    response = update_wishlist_item(event, sample_profile["id"], item_id)

    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["name"] == "Updated Name"
    assert body["description"] == "New description"


def test_update_wishlist_item_wrong_owner(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test that users cannot update other users' items."""
    # Create an item owned by sample_profile
    result = execute_query(
        "INSERT INTO wishlist_items (user_id, name, rank) VALUES (%s, %s, %s) RETURNING id",
        (sample_profile["id"], "Someone else's item", 0),
        fetch_one=True
    )
    item_id = str(result["id"])

    # Try to update as different user
    other_user_id = str(uuid4())

    from handlers.wishlist import update_wishlist_item

    event = {
        "body": json.dumps({
            "name": "Hacked Name"
        })
    }

    response = update_wishlist_item(event, other_user_id, item_id)

    assert response["statusCode"] == 403


def test_delete_wishlist_item(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test deleting a wishlist item."""
    # Create an item
    result = execute_query(
        "INSERT INTO wishlist_items (user_id, name, rank) VALUES (%s, %s, %s) RETURNING id",
        (sample_profile["id"], "Item to delete", 0),
        fetch_one=True
    )
    item_id = str(result["id"])

    from handlers.wishlist import delete_wishlist_item

    response = delete_wishlist_item(sample_profile["id"], item_id)

    assert response["statusCode"] == 204

    # Verify deletion
    item = execute_query(
        "SELECT * FROM wishlist_items WHERE id = %s",
        (item_id,),
        fetch_one=True
    )
    assert item is None


def test_reorder_wishlist_items(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test reordering wishlist items."""
    # Create multiple items
    item_ids = []
    for i in range(3):
        result = execute_query(
            "INSERT INTO wishlist_items (user_id, name, rank) VALUES (%s, %s, %s) RETURNING id",
            (sample_profile["id"], f"Item {i}", i),
            fetch_one=True
        )
        item_ids.append(str(result["id"]))

    from handlers.wishlist import reorder_wishlist_items

    event = {
        "body": json.dumps({
            "items": [
                {"id": item_ids[2], "rank": 0},
                {"id": item_ids[0], "rank": 1},
                {"id": item_ids[1], "rank": 2},
            ]
        })
    }

    response = reorder_wishlist_items(event, sample_profile["id"])

    assert response["statusCode"] == 200

    # Verify ranks in database
    for i, item_id in enumerate([item_ids[2], item_ids[0], item_ids[1]]):
        item = execute_query(
            "SELECT rank FROM wishlist_items WHERE id = %s",
            (item_id,),
            fetch_one=True
        )
        assert item["rank"] == i


def test_purchase_item(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test claiming an item as purchased."""
    # Create another user
    buyer_id = str(uuid4())
    execute_update(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (buyer_id, f"buyer-{uuid4()}@example.com", "Buyer User")
    )
    execute_update(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (buyer_id, sample_group["id"], "member")
    )

    # Create item owned by sample_profile
    result = execute_query(
        "INSERT INTO wishlist_items (user_id, name, rank) VALUES (%s, %s, %s) RETURNING id",
        (sample_profile["id"], "Item to purchase", 0),
        fetch_one=True
    )
    item_id = str(result["id"])

    execute_update(
        "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
        (item_id, sample_group["id"])
    )

    from handlers.purchases import claim_item

    event = {
        "body": json.dumps({
            "item_id": item_id,
            "group_id": sample_group["id"]
        })
    }

    response = claim_item(event, buyer_id)

    assert response["statusCode"] == 201

    body = json.loads(response["body"])
    assert body["item_id"] == item_id
    assert body["purchased_by"] == buyer_id

    # Verify in database
    purchase = execute_query(
        "SELECT * FROM purchases WHERE item_id = %s AND group_id = %s",
        (item_id, sample_group["id"]),
        fetch_one=True
    )
    assert purchase is not None
    assert str(purchase["purchased_by"]) == buyer_id


def test_cannot_purchase_own_item(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test that users cannot purchase their own items."""
    # Create item owned by sample_profile
    result = execute_query(
        "INSERT INTO wishlist_items (user_id, name, rank) VALUES (%s, %s, %s) RETURNING id",
        (sample_profile["id"], "My own item", 0),
        fetch_one=True
    )
    item_id = str(result["id"])

    execute_update(
        "INSERT INTO item_group_assignments (item_id, group_id) VALUES (%s, %s)",
        (item_id, sample_group["id"])
    )

    from handlers.purchases import claim_item

    event = {
        "body": json.dumps({
            "item_id": item_id,
            "group_id": sample_group["id"]
        })
    }

    response = claim_item(event, sample_profile["id"])

    assert response["statusCode"] == 403
