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
import boto3
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

# S3 Configuration
S3_BUCKET = os.getenv("PHOTOS_BUCKET", "presently-photos-dev-us-east-1-479453697367")


def create_test_image(color: tuple, text: str, size=(400, 400)) -> bytes:
    """
    Create a simple colored test image with text using PIL.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io

        # Create image with colored background
        img = Image.new('RGB', size, color=color)
        draw = ImageDraw.Draw(img)

        # Add text
        try:
            # Try to use a nice font
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            # Fallback to default font
            font = ImageFont.load_default()

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)

        # Draw text with shadow for better visibility
        shadow_offset = 2
        draw.text((position[0] + shadow_offset, position[1] + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
        draw.text(position, text, font=font, fill=(255, 255, 255))

        # Convert to JPEG bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)

        return img_bytes.read()

    except ImportError:
        print("   ⚠️  PIL not installed, using minimal JPEG")
        # Fallback to minimal JPEG
        return bytes.fromhex(
            'ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707'
            '070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c'
            '1c2837292c30313434341f27393d38323c2e333432ffdb0043010909090c0b0c180d'
            '0d1832211c213232323232323232323232323232323232323232323232323232323232'
            '32323232323232323232323232323232323232323232ffc00011080001000103011100'
            '02110103011100ffc4001500010100000000000000000000000000000000ffc40014100100'
            '00000000000000000000000000ffc400150001010000000000000000000000000000'
            '00ffc4001411010000000000000000000000000000000000ffda000c03010002110311'
            '003f00bf800000ffd9'
        )


def upload_test_image_to_s3(key: str, color: tuple, text: str) -> str:
    """
    Upload a test image to S3 and return the S3 key (not a URL).
    The backend will generate presigned URLs on-demand.
    Creates a colored image with text.
    """
    import io

    try:
        s3_client = boto3.client("s3")

        # Create test image
        img_bytes = create_test_image(color, text)

        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=img_bytes,
            ContentType='image/jpeg'
        )

        # Return just the S3 key, not a full URL
        # Format: s3://bucket-name/key
        return f"s3://{S3_BUCKET}/{key}"
    except Exception as e:
        print(f"   ⚠️  Warning: Could not upload test image to S3: {e}")
        print(f"   Using placeholder URL instead")
        return None


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

        # Upload test images to S3
        print("   📸 Uploading test images to S3...")
        photo_url_1 = upload_test_image_to_s3("seed-data/headphones.jpg", (70, 130, 180), "🎧\nHeadphones")
        photo_url_2 = upload_test_image_to_s3("seed-data/yoga-mat.jpg", (147, 112, 219), "🧘\nYoga Mat")
        photo_url_3 = upload_test_image_to_s3("seed-data/smartwatch.jpg", (255, 99, 71), "⌚\nSmart Watch")
        if photo_url_1:
            print(f"   ✓ Uploaded headphones.jpg")
        if photo_url_2:
            print(f"   ✓ Uploaded yoga-mat.jpg")
        if photo_url_3:
            print(f"   ✓ Uploaded smartwatch.jpg")

        # Alice's wishlist items (shared with Family)
        alice_items = [
            {
                "name": "Wireless Headphones",
                "description": "Noise-cancelling, Bluetooth, over-ear",
                "url": "https://example.com/headphones",
                "price": 299.99,
                "rank": 1,
                "photo_url": photo_url_1,
            },
            {
                "name": "Yoga Mat",
                "description": "Extra thick, non-slip surface",
                "url": "https://example.com/yoga-mat",
                "price": 45.00,
                "rank": 2,
                "photo_url": photo_url_2,
            },
            {
                "name": "Recipe Book",
                "description": "Mediterranean cuisine cookbook",
                "url": None,
                "price": 29.99,
                "rank": 3,
                "photo_url": None,
            },
        ]

        alice_item_ids = []
        for item in alice_items:
            item_id = str(uuid4())
            alice_item_ids.append(item_id)
            cur.execute(
                """
                INSERT INTO wishlist_items (id, user_id, name, description, url, price, photo_url, rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    item_id,
                    USERS[0]["id"],
                    item["name"],
                    item["description"],
                    item["url"],
                    item["price"],
                    item["photo_url"],
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
                "photo_url": photo_url_3,
                "groups": [family_group_id, work_group_id],  # Share with multiple groups
            },
            {
                "name": "Coffee Maker",
                "description": "Programmable, thermal carafe",
                "url": "https://example.com/coffee",
                "price": 149.99,
                "rank": 2,
                "photo_url": None,
                "groups": [family_group_id],
            },
            {
                "name": "Desk Lamp",
                "description": "LED, adjustable brightness",
                "url": None,
                "price": 79.99,
                "rank": 3,
                "photo_url": None,
                "groups": [work_group_id],
            },
        ]

        bob_item_ids = []
        for item in bob_items:
            item_id = str(uuid4())
            bob_item_ids.append(item_id)
            cur.execute(
                """
                INSERT INTO wishlist_items (id, user_id, name, description, url, price, photo_url, rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    item_id,
                    USERS[1]["id"],
                    item["name"],
                    item["description"],
                    item["url"],
                    item["price"],
                    item["photo_url"],
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
