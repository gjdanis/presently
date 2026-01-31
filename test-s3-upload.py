#!/usr/bin/env python3
"""
Test S3 photo upload functionality
"""

import boto3
import uuid
import os
from datetime import datetime

# Configuration
BUCKET_NAME = "presently-photos-dev-us-east-1-479453697367"
TEST_USER_ID = "test-user-123"

def test_s3_upload():
    """Test generating presigned URL and uploading to S3"""

    print(f"📦 Testing S3 upload to bucket: {BUCKET_NAME}\n")

    # Create S3 client
    s3_client = boto3.client("s3")

    # Generate unique filename
    file_key = f"uploads/{TEST_USER_ID}/{uuid.uuid4()}.jpg"
    print(f"📝 Generated file key: {file_key}")

    # Generate presigned POST URL
    try:
        presigned_post = s3_client.generate_presigned_post(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Fields={"Content-Type": "image/jpeg"},
            Conditions=[
                {"Content-Type": "image/jpeg"},
                ["content-length-range", 0, 5242880],  # Max 5MB
            ],
            ExpiresIn=3600,  # 1 hour
        )

        print(f"✅ Presigned POST URL generated successfully")
        print(f"\nUpload URL: {presigned_post['url']}")
        print(f"\nFields:")
        for key, value in presigned_post['fields'].items():
            print(f"  {key}: {value}")

        # Construct the file URL
        file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_key}"
        print(f"\n🌐 File URL (after upload): {file_url}")

        return presigned_post, file_url

    except Exception as e:
        print(f"❌ Error generating presigned URL: {e}")
        return None, None

def list_bucket_contents():
    """List contents of the S3 bucket"""
    print(f"\n📂 Listing bucket contents...\n")

    s3_client = boto3.client("s3")

    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix="uploads/",
            MaxKeys=10
        )

        if 'Contents' in response:
            print(f"Found {len(response['Contents'])} file(s):\n")
            for obj in response['Contents']:
                size_kb = obj['Size'] / 1024
                print(f"  📄 {obj['Key']}")
                print(f"     Size: {size_kb:.2f} KB")
                print(f"     Modified: {obj['LastModified']}")
                print()
        else:
            print("  (empty)")

    except Exception as e:
        print(f"❌ Error listing bucket: {e}")

def create_test_image():
    """Create a simple test image file"""
    import io

    print("\n🎨 Creating test image...")

    # Create a minimal valid JPEG file (1x1 pixel)
    # This is a valid JPEG header + minimal image data
    jpeg_bytes = bytes.fromhex(
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

    img_bytes = io.BytesIO(jpeg_bytes)

    print("✅ Test image created (minimal 1x1 JPEG)")

    return img_bytes

def upload_test_image_directly():
    """Upload a test image directly to S3"""
    print("\n🚀 Testing direct S3 upload...\n")

    s3_client = boto3.client("s3")

    # Create test image
    img_bytes = create_test_image()

    # Generate filename
    file_key = f"uploads/{TEST_USER_ID}/test-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jpg"

    try:
        # Upload directly
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=img_bytes,
            ContentType='image/jpeg'
        )

        file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_key}"

        print(f"✅ Image uploaded successfully!")
        print(f"📄 Key: {file_key}")
        print(f"🌐 URL: {file_url}")

        # Generate a presigned URL for viewing (since bucket is private)
        view_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600
        )

        print(f"\n👁️  View URL (expires in 1 hour):")
        print(f"{view_url}")

        return file_url, view_url

    except Exception as e:
        print(f"❌ Error uploading: {e}")
        return None, None

if __name__ == "__main__":
    print("=" * 70)
    print("  S3 Photo Upload Test")
    print("=" * 70)

    # Test 1: Generate presigned URL
    presigned_post, file_url = test_s3_upload()

    # Test 2: List bucket contents
    list_bucket_contents()

    # Test 3: Upload a real test image
    upload_url, view_url = upload_test_image_directly()

    print("\n" + "=" * 70)
    print("  Test Complete")
    print("=" * 70)
