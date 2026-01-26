#!/usr/bin/env python3
"""
Seed local database with test data for development.
Creates 3 users with different combinations of groups, items, and purchases.
"""

import os
import sys
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

# Load local environment variables
env_path = Path(__file__).parent.parent.parent / ".env.local"
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"❌ Error: {env_path} not found")
    print("   Copy .env.local.example to .env.local and configure DATABASE_URL")
    sys.exit(1)

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ Error: DATABASE_URL not set in .env.local")
    sys.exit(1)

# Test users (UUIDs that would come from Cognito)
USERS = [
    {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "email": "alice@example.com",
        "name": "Alice Johnson",
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "email": "bob@example.com",
        "name": "Bob Smith",
    },
    {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "email": "charlie@example.com",
        "name": "Charlie Davis",
    },
]


def seed_database():
    """Seed the database with test data."""
    print("🌱 Seeding local database with test data...")
    print(f"📍 Database: {DATABASE_URL.split('@')[-1]}\n")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Clear existing data
        print("🧹 Clearing existing data...")
        cur.execute("DELETE FROM purchases")
        cur.execute("DELETE FROM item_group_assignments")
        cur.execute("DELETE FROM group_invitations")
        cur.execute("DELETE FROM wishlist_items")
        cur.execute("DELETE FROM group_memberships")
        cur.execute("DELETE FROM groups")
        cur.execute("DELETE FROM profiles")
        conn.commit()
        print("✅ Existing data cleared\n")

        # Create users
        print("👥 Creating users...")
        for user in USERS:
            cur.execute(
                """
                INSERT INTO profiles (id, email, name)
                VALUES (%s, %s, %s)
                """,
                (user["id"], user["email"], user["name"]),
            )
            print(f"   ✓ {user['name']} ({user['email']})")
        conn.commit()
        print()

        # Create groups with different membership patterns
        print("👨‍👩‍👧‍👦 Creating groups...")

        # Group 1: Family - Alice (admin), Bob, Charlie
        family_group_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO groups (id, name, description, created_by)
            VALUES (%s, %s, %s, %s)
            """,
            (family_group_id, "Family", "Johnson Family Gift Exchange", USERS[0]["id"]),
        )
        for i, role in enumerate(["admin", "member", "member"]):
            cur.execute(
                """
                INSERT INTO group_memberships (user_id, group_id, role)
                VALUES (%s, %s, %s)
                """,
                (USERS[i]["id"], family_group_id, role),
            )
        print(f"   ✓ Family (Alice, Bob, Charlie)")

        # Group 2: Work Friends - Bob (admin), Alice
        work_group_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO groups (id, name, description, created_by)
            VALUES (%s, %s, %s, %s)
            """,
            (work_group_id, "Work Friends", "Holiday gift exchange at work", USERS[1]["id"]),
        )
        cur.execute(
            """
            INSERT INTO group_memberships (user_id, group_id, role)
            VALUES (%s, %s, %s)
            """,
            (USERS[1]["id"], work_group_id, "admin"),
        )
        cur.execute(
            """
            INSERT INTO group_memberships (user_id, group_id, role)
            VALUES (%s, %s, %s)
            """,
            (USERS[0]["id"], work_group_id, "member"),
        )
        print(f"   ✓ Work Friends (Bob, Alice)")

        # Group 3: Book Club - Charlie (admin), Bob
        book_group_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO groups (id, name, description, created_by)
            VALUES (%s, %s, %s, %s)
            """,
            (book_group_id, "Book Club", "Monthly book club members", USERS[2]["id"]),
        )
        cur.execute(
            """
            INSERT INTO group_memberships (user_id, group_id, role)
            VALUES (%s, %s, %s)
            """,
            (USERS[2]["id"], book_group_id, "admin"),
        )
        cur.execute(
            """
            INSERT INTO group_memberships (user_id, group_id, role)
            VALUES (%s, %s, %s)
            """,
            (USERS[1]["id"], book_group_id, "member"),
        )
        print(f"   ✓ Book Club (Charlie, Bob)")
        conn.commit()
        print()

        # Create wishlist items for each user
        print("🎁 Creating wishlist items...")

        # Alice's wishlist items (shared with Family)
        alice_items = [
            {
                "name": "Wireless Headphones",
                "description": "Noise-cancelling, Bluetooth, over-ear",
                "url": "https://example.com/headphones",
                "price": 299.99,
                "rank": 1,
            },
            {
                "name": "Yoga Mat",
                "description": "Extra thick, non-slip surface",
                "url": "https://example.com/yoga-mat",
                "price": 45.00,
                "rank": 2,
            },
            {
                "name": "Recipe Book",
                "description": "Mediterranean cuisine cookbook",
                "url": None,
                "price": 29.99,
                "rank": 3,
            },
        ]

        alice_item_ids = []
        for item in alice_items:
            item_id = str(uuid4())
            alice_item_ids.append(item_id)
            cur.execute(
                """
                INSERT INTO wishlist_items (id, user_id, name, description, url, price, rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    item_id,
                    USERS[0]["id"],
                    item["name"],
                    item["description"],
                    item["url"],
                    item["price"],
                    item["rank"],
                ),
            )
            # Share with Family group
            cur.execute(
                """
                INSERT INTO item_group_assignments (item_id, group_id)
                VALUES (%s, %s)
                """,
                (item_id, family_group_id),
            )
        print(f"   ✓ Alice: {len(alice_items)} items (Family)")

        # Bob's wishlist items (shared with Family and Work)
        bob_items = [
            {
                "name": "Smart Watch",
                "description": "Fitness tracking, GPS, waterproof",
                "url": "https://example.com/smartwatch",
                "price": 399.99,
                "rank": 1,
                "groups": [family_group_id, work_group_id],  # Share with multiple groups
            },
            {
                "name": "Coffee Maker",
                "description": "Programmable, thermal carafe",
                "url": "https://example.com/coffee",
                "price": 149.99,
                "rank": 2,
                "groups": [family_group_id],
            },
            {
                "name": "Desk Lamp",
                "description": "LED, adjustable brightness",
                "url": None,
                "price": 79.99,
                "rank": 3,
                "groups": [work_group_id],
            },
        ]

        bob_item_ids = []
        for item in bob_items:
            item_id = str(uuid4())
            bob_item_ids.append(item_id)
            cur.execute(
                """
                INSERT INTO wishlist_items (id, user_id, name, description, url, price, rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    item_id,
                    USERS[1]["id"],
                    item["name"],
                    item["description"],
                    item["url"],
                    item["price"],
                    item["rank"],
                ),
            )
            # Share with specified groups
            for group_id in item["groups"]:
                cur.execute(
                    """
                    INSERT INTO item_group_assignments (item_id, group_id)
                    VALUES (%s, %s)
                    """,
                    (item_id, group_id),
                )
        print(f"   ✓ Bob: {len(bob_items)} items (Family, Work)")

        # Charlie's wishlist items (shared with Family and Book Club)
        charlie_items = [
            {
                "name": "Reading Tablet",
                "description": "E-ink display, waterproof, 8GB",
                "url": "https://example.com/tablet",
                "price": 179.99,
                "rank": 1,
                "groups": [family_group_id, book_group_id],
            },
            {
                "name": "Hiking Backpack",
                "description": "40L capacity, waterproof",
                "url": "https://example.com/backpack",
                "price": 129.99,
                "rank": 2,
                "groups": [family_group_id],
            },
        ]

        charlie_item_ids = []
        for item in charlie_items:
            item_id = str(uuid4())
            charlie_item_ids.append(item_id)
            cur.execute(
                """
                INSERT INTO wishlist_items (id, user_id, name, description, url, price, rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    item_id,
                    USERS[2]["id"],
                    item["name"],
                    item["description"],
                    item["url"],
                    item["price"],
                    item["rank"],
                ),
            )
            # Share with specified groups
            for group_id in item["groups"]:
                cur.execute(
                    """
                    INSERT INTO item_group_assignments (item_id, group_id)
                    VALUES (%s, %s)
                    """,
                    (item_id, group_id),
                )
        print(f"   ✓ Charlie: {len(charlie_items)} items (Family, Book Club)")
        conn.commit()
        print()

        # Create some purchases to demonstrate claimed items
        print("🛒 Creating purchase claims...")

        # Bob claims Alice's headphones in Family group
        cur.execute(
            """
            INSERT INTO purchases (item_id, purchased_by, group_id)
            VALUES (%s, %s, %s)
            """,
            (alice_item_ids[0], USERS[1]["id"], family_group_id),
        )
        print(f"   ✓ Bob claimed Alice's Wireless Headphones")

        # Alice claims Bob's Smart Watch in Work group
        cur.execute(
            """
            INSERT INTO purchases (item_id, purchased_by, group_id)
            VALUES (%s, %s, %s)
            """,
            (bob_item_ids[0], USERS[0]["id"], work_group_id),
        )
        print(f"   ✓ Alice claimed Bob's Smart Watch (Work)")

        # Charlie claims Bob's Coffee Maker in Family group
        cur.execute(
            """
            INSERT INTO purchases (item_id, purchased_by, group_id)
            VALUES (%s, %s, %s)
            """,
            (bob_item_ids[1], USERS[2]["id"], family_group_id),
        )
        print(f"   ✓ Charlie claimed Bob's Coffee Maker")

        conn.commit()
        print()

        # Print summary
        print("="*60)
        print("✅ Database seeded successfully!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   • {len(USERS)} users created")
        print(f"   • 3 groups created (Family, Work Friends, Book Club)")
        print(f"   • 8 wishlist items created")
        print(f"   • 3 purchases claimed")
        print()
        print("🔐 Test Users (use these for local Cognito bypass):")
        for user in USERS:
            print(f"   • {user['name']}: {user['email']}")
            print(f"     ID: {user['id']}")
        print()
        print("💡 Next steps:")
        print("   1. Start the frontend: make frontend")
        print("   2. Start the backend: make backend")
        print("   3. Login as one of the test users")
        print()

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed_database()
