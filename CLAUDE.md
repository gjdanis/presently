# Presently - AWS Migration Plan

## Executive Summary

This document provides a complete specification for migrating Presently from Supabase to AWS infrastructure optimized for **maximum free tier usage**. The new architecture uses:

- **Frontend**: Next.js (React) on Vercel (Free tier)
- **Backend**: Python AWS Lambda + API Gateway (Free tier: 1M requests/month)
- **Auth**: AWS Cognito (Free tier: 50k MAU)
- **Database**: Neon Postgres (Free tier: 0.5GB storage, 3GB data transfer)
- **Infrastructure**: CloudFormation for IaC
- **Storage**: S3 for photo uploads (~$1-2/month)

**Expected Monthly Cost: $0-2** for personal/family use (< 1M requests/month)

### Key Architecture Decisions

**Why Neon instead of RDS?**
- ✅ **Free tier**: 0.5GB storage (enough for thousands of wishlist items)
- ✅ **No RLS complexity**: All authorization in Lambda code (you control everything)
- ✅ **Simple setup**: No VPC, subnets, security groups
- ✅ **Instant branching**: Free dev/staging database copies
- ✅ **Auto-scaling**: Scales to zero when idle
- ✅ **Cost**: $0/month for low usage vs $14-40/month for RDS

**Monorepo Structure**: Frontend and backend in single repository for easier management

---

## 0. Repository Structure (Monorepo)

```
presently/
├── README.md
├── .gitignore
├── infrastructure/
│   ├── cloudformation/
│   │   ├── cognito-s3.yaml         # Cognito User Pool + S3 bucket
│   │   └── api-lambda.yaml         # API Gateway + Lambda functions
│   └── scripts/
│       ├── deploy-infra.sh
│       └── deploy-lambda.sh
├── backend/
│   ├── lambda/
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Cognito JWT verification
│   │   │   ├── db.py               # Neon Postgres connection
│   │   │   ├── responses.py        # Standard HTTP responses
│   │   │   └── validators.py       # Request validation
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # POST /auth/*
│   │   │   ├── groups.py           # CRUD /groups/*
│   │   │   ├── wishlist.py         # CRUD /wishlist/*
│   │   │   ├── purchases.py        # CRUD /purchases/*
│   │   │   ├── invitations.py      # GET/POST /invitations/*
│   │   │   ├── photos.py           # POST /photos/upload
│   │   │   └── link_preview.py     # GET /link-preview
│   │   ├── requirements.txt
│   │   └── template.yaml           # SAM template for Lambda deployment
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_groups.py
│   │   └── test_wishlist.py
│   └── migrations/
│       └── schema.sql               # Database schema
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── auth/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   ├── groups/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── new/page.tsx
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx
│   │   │   │       └── manage/page.tsx
│   │   │   └── wishlists/
│   │   │       ├── page.tsx
│   │   │       ├── new/page.tsx
│   │   │       └── [id]/edit/page.tsx
│   │   └── invite/[token]/page.tsx
│   ├── components/
│   │   ├── ui/
│   │   ├── DashboardNav.tsx
│   │   ├── WishlistItemCard.tsx
│   │   ├── CollapsibleWishlistSection.tsx
│   │   └── ...
│   ├── lib/
│   │   ├── api.ts                  # API client (calls Lambda)
│   │   ├── auth.ts                 # Cognito auth helpers
│   │   └── hooks/
│   │       ├── useAuth.ts
│   │       ├── useGroups.ts
│   │       └── useWishlist.ts
│   ├── styles/
│   │   └── globals.css
│   ├── public/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── .github/
│   └── workflows/
│       ├── deploy-backend.yml
│       └── deploy-frontend.yml
└── package.json                    # Root scripts (optional)
```

### Benefits of Monorepo:
- Single source of truth for both frontend and backend
- Easier version control and deployments
- Can share types/constants between frontend and backend
- Atomic commits across full-stack features
- Simplified CI/CD pipelines

---

## 1. Application Overview

### 1.1 What is Presently?

A multi-group wishlist application where:
- Users create wishlists with items they want
- Users belong to multiple groups (family, friends, coworkers)
- Group members can see each other's wishlists
- Members can secretly mark items as "purchased" without the owner knowing
- Privacy is enforced: owners cannot see who purchased their items or purchase status

### 1.2 Core User Flows

#### Flow 1: New User Registration & First Group
1. User visits landing page
2. Clicks "Sign Up"
3. Enters name, email, password
4. Confirms email via Cognito verification
5. Redirected to dashboard
6. Creates first group (e.g., "Smith Family")
7. Becomes admin of that group
8. Invites family members via email

#### Flow 2: Accepting an Invitation
1. User receives email with invitation link
2. Clicks link → lands on `/invite/{token}` page
3. If not registered: sees signup form with group details
4. If already registered: logs in
5. System automatically adds user to the group
6. User is redirected to group page

#### Flow 3: Creating a Wishlist Item
1. User navigates to "My Wishlists"
2. Clicks "Add Item"
3. Enters:
   - Item name (required)
   - Description (optional)
   - URL/link (optional)
   - Price (optional)
   - Photo upload (optional)
4. Selects which group(s) to share with
5. Can drag-and-drop to reorder priority
6. Saves item

#### Flow 4: Viewing Group Wishlists & Purchasing
1. User selects a group from navigation
2. Sees list of all members
3. Sees collapsible sections for each member's wishlist
4. **If viewing own items**: Cannot see purchase status
5. **If viewing others' items**:
   - Can see if item is already purchased (by someone else)
   - Can click "Mark as Purchased" to claim item
   - Claimed items are hidden from the owner but visible to other members
6. Can un-claim items if needed

#### Flow 5: Managing a Group (Admin Only)
1. Group admin clicks "Manage Group"
2. Can:
   - View all members
   - Send new invitations
   - Remove members
   - Edit group name/description
   - Delete group (with confirmation)

---

## 2. Database Schema

### 2.1 PostgreSQL Tables

```sql
-- Users table (managed by Cognito, but we store extended profile data)
CREATE TABLE profiles (
  id UUID PRIMARY KEY,  -- Cognito User Sub (UUID)
  email TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_profiles_email ON profiles(email);

-- Groups
CREATE TABLE groups (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  created_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_groups_created_by ON groups(created_by);

-- Group Memberships (many-to-many: users <-> groups)
CREATE TABLE group_memberships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('admin', 'member')),
  joined_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, group_id)
);
CREATE INDEX idx_group_memberships_user_id ON group_memberships(user_id);
CREATE INDEX idx_group_memberships_group_id ON group_memberships(group_id);

-- Wishlist Items
CREATE TABLE wishlist_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  url TEXT,
  price NUMERIC(10,2),
  photo_url TEXT,  -- S3 URL
  rank INTEGER DEFAULT 0,  -- For drag-and-drop ordering
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_wishlist_items_user_id ON wishlist_items(user_id);
CREATE INDEX idx_wishlist_items_rank ON wishlist_items(user_id, rank DESC);

-- Item-Group Assignments (items can be shared with multiple groups)
CREATE TABLE item_group_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  item_id UUID NOT NULL REFERENCES wishlist_items(id) ON DELETE CASCADE,
  group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(item_id, group_id)
);
CREATE INDEX idx_item_group_assignments_item_id ON item_group_assignments(item_id);
CREATE INDEX idx_item_group_assignments_group_id ON item_group_assignments(group_id);

-- Purchases (who claimed what item in which group context)
CREATE TABLE purchases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  item_id UUID NOT NULL REFERENCES wishlist_items(id) ON DELETE CASCADE,
  purchased_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  purchased_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(item_id, group_id)  -- One claim per item per group
);
CREATE INDEX idx_purchases_item_id ON purchases(item_id);
CREATE INDEX idx_purchases_purchased_by ON purchases(purchased_by);
CREATE INDEX idx_purchases_group_id ON purchases(group_id);

-- Group Invitations
CREATE TABLE group_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  invited_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  email TEXT NOT NULL,  -- Email of invitee (may not be registered yet)
  role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('admin', 'member')),
  token TEXT NOT NULL UNIQUE,  -- Random token for invite link
  accepted_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(group_id, email)
);
CREATE INDEX idx_group_invitations_token ON group_invitations(token);
CREATE INDEX idx_group_invitations_email ON group_invitations(email);
CREATE INDEX idx_group_invitations_group_id ON group_invitations(group_id);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_groups_updated_at
  BEFORE UPDATE ON groups
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_wishlist_items_updated_at
  BEFORE UPDATE ON wishlist_items
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### 2.2 Data Access Patterns & Authorization Rules

**Rule 1: Users can only access groups they're members of**
- Check `group_memberships` table before returning group data

**Rule 2: Wishlist items visibility**
- Users can see items that are assigned to their groups
- Query: Join `item_group_assignments` with user's `group_memberships`

**Rule 3: Purchase privacy**
- Item owners CANNOT see purchases of their own items
- Other group members CAN see purchases
- Implementation: Filter purchases WHERE `item.user_id != current_user.id`

**Rule 4: Admin permissions**
- Only group admins can invite/remove members
- Check `role = 'admin'` in `group_memberships`

**Rule 5: Item ownership**
- Users can only edit/delete their own wishlist items
- Check `wishlist_items.user_id = current_user.id`

---

## 3. API Specification

### 3.1 Authentication

All API requests (except public endpoints) require:
```
Authorization: Bearer <JWT_TOKEN_FROM_COGNITO>
```

Lambda functions will verify JWT using Cognito public keys.

### 3.2 API Endpoints

#### Authentication & Profile

**POST /auth/register**
```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe"
}

// Response 201
{
  "userId": "uuid",
  "email": "user@example.com"
}
```

**POST /auth/login** (Handled by Cognito, returns JWT)

**GET /profile**
```json
// Response 200
{
  "id": "uuid",
  "name": "John Doe",
  "email": "user@example.com",
  "createdAt": "2026-01-15T10:00:00Z"
}
```

**PUT /profile**
```json
// Request
{
  "name": "John Smith"
}

// Response 200
{
  "id": "uuid",
  "name": "John Smith",
  "email": "user@example.com"
}
```

#### Groups

**GET /groups**
```json
// Response 200
{
  "groups": [
    {
      "id": "uuid",
      "name": "Smith Family",
      "description": "Our family wishlist group",
      "role": "admin",
      "memberCount": 5,
      "createdAt": "2026-01-01T00:00:00Z"
    }
  ]
}
```

**POST /groups**
```json
// Request
{
  "name": "Work Friends",
  "description": "Holiday gift exchange"
}

// Response 201
{
  "id": "uuid",
  "name": "Work Friends",
  "description": "Holiday gift exchange",
  "role": "admin"
}
```

**GET /groups/{groupId}**
```json
// Response 200
{
  "group": {
    "id": "uuid",
    "name": "Smith Family",
    "description": "..."
  },
  "members": [
    {
      "userId": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      "role": "admin",
      "joinedAt": "2026-01-01T00:00:00Z"
    }
  ],
  "wishlists": [
    {
      "userId": "uuid",
      "userName": "Jane Doe",
      "items": [
        {
          "id": "uuid",
          "name": "Headphones",
          "description": "Noise-cancelling",
          "url": "https://...",
          "price": 299.99,
          "photoUrl": "https://s3.../image.jpg",
          "rank": 0,
          "isPurchased": false,  // Hidden if viewing own items
          "purchasedBy": null     // Hidden if viewing own items
        }
      ]
    }
  ]
}
```

**PUT /groups/{groupId}**
```json
// Request
{
  "name": "Updated Name",
  "description": "Updated description"
}

// Response 200
{
  "id": "uuid",
  "name": "Updated Name",
  "description": "Updated description"
}
```

**DELETE /groups/{groupId}**
```
// Response 204 No Content
```

**POST /groups/{groupId}/members**
```json
// Request
{
  "email": "friend@example.com"
}

// Response 201
{
  "addedDirectly": false,
  "inviteUrl": "https://presently.com/invite/{token}",
  "emailSent": true
}
```

**DELETE /groups/{groupId}/members/{userId}**
```
// Response 204 No Content
```

#### Wishlist Items

**GET /wishlist**
```json
// Response 200
{
  "items": [
    {
      "id": "uuid",
      "name": "Headphones",
      "description": "...",
      "url": "https://...",
      "price": 299.99,
      "photoUrl": "https://s3.../image.jpg",
      "rank": 0,
      "groups": [
        {
          "id": "uuid",
          "name": "Smith Family"
        }
      ],
      "createdAt": "2026-01-15T00:00:00Z"
    }
  ]
}
```

**POST /wishlist**
```json
// Request
{
  "name": "New Item",
  "description": "Description",
  "url": "https://amazon.com/...",
  "price": 49.99,
  "photoUrl": null,
  "groupIds": ["uuid1", "uuid2"]
}

// Response 201
{
  "id": "uuid",
  "name": "New Item",
  ...
}
```

**GET /wishlist/{itemId}**
**PUT /wishlist/{itemId}**
**DELETE /wishlist/{itemId}**

**PUT /wishlist/reorder**
```json
// Request
{
  "items": [
    { "id": "uuid1", "rank": 0 },
    { "id": "uuid2", "rank": 1 },
    { "id": "uuid3", "rank": 2 }
  ]
}

// Response 200
{ "success": true }
```

#### Purchases

**POST /purchases**
```json
// Request
{
  "itemId": "uuid",
  "groupId": "uuid"
}

// Response 201
{
  "id": "uuid",
  "itemId": "uuid",
  "groupId": "uuid",
  "purchasedAt": "2026-01-20T10:00:00Z"
}
```

**DELETE /purchases/{itemId}/{groupId}**
```
// Response 204 No Content
```

#### Invitations

**GET /invitations/{token}**
```json
// Response 200
{
  "groupId": "uuid",
  "groupName": "Smith Family",
  "groupDescription": "...",
  "invitedBy": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "role": "member",
  "expiresAt": "2026-01-30T00:00:00Z"
}
```

**POST /invitations/{token}/accept**
```json
// Response 200
{
  "groupId": "uuid",
  "alreadyMember": false
}
```

#### Photo Upload

**POST /photos/upload**
```json
// Request (multipart/form-data)
// file: <binary image data>

// Response 201
{
  "url": "https://s3.amazonaws.com/presently-photos/uuid.jpg"
}
```

#### Link Preview (for wishlist URLs)

**GET /link-preview?url={encoded_url}**
```json
// Response 200
{
  "title": "Product Name",
  "description": "Product description",
  "image": "https://...",
  "price": "$299.99"
}
```

---

## 4. AWS Architecture

### 4.1 Infrastructure Components

```
┌─────────────┐
│   Vercel    │  Next.js Frontend (Free tier)
│  (Frontend) │
└──────┬──────┘
       │ HTTPS
       ▼
┌──────────────┐      ┌────────────────┐
│ API Gateway  │      │  CloudFront +  │
│   (REST)     │      │       S3       │
│  Free Tier   │      │  (Photos CDN)  │
└──────┬───────┘      └────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Lambda Functions (Python)   │
│  Free Tier: 1M requests/mo   │
│  - auth.py                   │
│  - groups.py                 │
│  - wishlist.py               │
│  - purchases.py              │
│  - invitations.py            │
│  - photos.py                 │
└──────┬───────────────────────┘
       │
   ┌───┴────┬────────────┐
   │        │            │
   ▼        ▼            ▼
┌────────┐ ┌─────┐ ┌─────────┐
│Cognito │ │ Neon│ │   S3    │
│  FREE  │ │ FREE│ │ ~$1/mo  │
└────────┘ └─────┘ └─────────┘
         Postgres
      (0.5GB storage)
```

### 4.2 Services Used & Free Tier Limits

1. **Vercel** (Frontend) - **FREE**
   - Unlimited bandwidth
   - Automatic SSL
   - Edge network
   - Preview deployments

2. **AWS Cognito** (Authentication) - **FREE**
   - Free tier: 50,000 MAU (Monthly Active Users)
   - Email/password authentication
   - JWT token generation
   - Email verification
   - **Cost**: $0 for personal/family use

3. **AWS API Gateway** (REST API) - **FREE (1M requests)**
   - Free tier: 1 million API calls/month (12 months)
   - After: $3.50 per million requests
   - Lambda proxy integration
   - Cognito authorizer
   - CORS configuration
   - **Cost**: $0 for < 1M requests/month

4. **AWS Lambda** (Backend) - **FREE (1M requests)**
   - Free tier (permanent): 1M requests/month + 400,000 GB-seconds compute
   - Python 3.11 runtime
   - 512MB memory per function
   - Serverless scaling
   - **Cost**: $0 for < 1M requests/month

5. **Neon Postgres** (Database) - **FREE**
   - Free tier: 0.5GB storage, 3GB data transfer/month
   - Serverless Postgres
   - Auto-scaling (scales to zero)
   - Instant database branching (dev/staging copies)
   - No VPC setup required
   - **Cost**: $0 for < 0.5GB storage

6. **AWS S3** (Photo Storage) - **~$1-2/month**
   - Storage: $0.023 per GB/month
   - PUT requests: $0.005 per 1,000 requests
   - GET requests: $0.0004 per 1,000 requests
   - Presigned URLs for uploads
   - **Cost**: $0.23 for 10GB photos + $1 for transfers = **~$1.23/month**

7. **AWS CloudFront** (CDN for photos) - **~$0.85/month**
   - First 10TB: $0.085 per GB
   - 10GB transfer: $0.85
   - **Cost**: **~$0.85** for 10GB photo delivery

8. **CloudFormation** (Infrastructure as Code) - **FREE**
   - No charge for CloudFormation itself
   - Only pay for resources created

9. **AWS SES** (Email - Optional) - **FREE (62,000 emails/month)**
   - Free tier: 62,000 emails/month when sending from EC2
   - For Lambda: $0.10 per 1,000 emails
   - Invitation emails via Cognito (free)
   - **Cost**: $0 for Cognito emails

### 4.3 Total Monthly Cost Breakdown

| Service | Free Tier | After Free Tier | Typical Cost |
|---------|-----------|-----------------|--------------|
| Vercel | ✅ FREE | FREE | **$0** |
| Cognito | 50k MAU | $0.0055/MAU | **$0** (< 50k users) |
| API Gateway | 1M requests | $3.50/M | **$0** (< 1M) |
| Lambda | 1M requests | $0.20/M | **$0** (< 1M) |
| Neon Postgres | 0.5GB storage | $0.102/GB | **$0** (< 0.5GB) |
| S3 Storage | 5GB | $0.023/GB | **$0.23** (10GB) |
| CloudFront | 1TB | $0.085/GB | **$0.85** (10GB) |
| **TOTAL** | | | **~$1-2/month** |

**Free tier remains free as long as:**
- < 50,000 monthly active users
- < 1 million API requests/month (~33k per day)
- < 0.5GB database storage (~thousands of wishlist items)
- Minimal photo uploads

**When you'd start paying:**
- **At 2M requests/month**: +$3.50/month (API Gateway)
- **At 0.6GB database**: +$0.01/month (Neon auto-scales pricing)
- **At 20GB photos**: +$1.50/month (S3 storage)

### 4.3 Lambda Function Structure

**Python Project Layout:**
```
lambda/
├── common/
│   ├── __init__.py
│   ├── auth.py          # Cognito JWT verification
│   ├── db.py            # Database connection helper
│   ├── responses.py     # Standard HTTP responses
│   └── validators.py    # Request validation
├── handlers/
│   ├── auth.py          # POST /auth/*
│   ├── groups.py        # CRUD /groups/*
│   ├── wishlist.py      # CRUD /wishlist/*
│   ├── purchases.py     # CRUD /purchases/*
│   ├── invitations.py   # GET/POST /invitations/*
│   ├── photos.py        # POST /photos/upload
│   └── link_preview.py  # GET /link-preview
├── requirements.txt
└── template.yaml        # SAM template (or CloudFormation)
```

**Example Lambda Handler (groups.py):**
```python
import json
import os
from common.auth import verify_token
from common.db import get_db_connection
from common.responses import success, error, unauthorized
from common.validators import validate_request

def handler(event, context):
    """
    Handles /groups/* endpoints
    """
    # Parse request
    http_method = event['httpMethod']
    path = event['path']
    user = verify_token(event['headers'].get('Authorization'))

    if not user:
        return unauthorized()

    # Route to appropriate function
    if http_method == 'GET' and path == '/groups':
        return get_groups(user['sub'])
    elif http_method == 'POST' and path == '/groups':
        return create_group(user['sub'], json.loads(event['body']))
    elif http_method == 'GET' and '/groups/' in path:
        group_id = path.split('/')[-1]
        return get_group_detail(user['sub'], group_id)
    # ... more routes

    return error('Not Found', 404)

def get_groups(user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Query groups where user is a member
    cur.execute("""
        SELECT g.id, g.name, g.description, gm.role, g.created_at,
               COUNT(DISTINCT gm2.user_id) as member_count
        FROM groups g
        JOIN group_memberships gm ON g.id = gm.group_id
        LEFT JOIN group_memberships gm2 ON g.id = gm2.group_id
        WHERE gm.user_id = %s
        GROUP BY g.id, g.name, g.description, gm.role, g.created_at
        ORDER BY g.created_at DESC
    """, (user_id,))

    groups = []
    for row in cur.fetchall():
        groups.append({
            'id': str(row[0]),
            'name': row[1],
            'description': row[2],
            'role': row[3],
            'memberCount': row[5],
            'createdAt': row[4].isoformat()
        })

    cur.close()
    conn.close()

    return success({'groups': groups})
```

### 4.4 Database Connection Handling

Use **Neon Postgres** connection string (no proxy needed):

```python
# common/db.py
import os
import psycopg2
from psycopg2 import pool

# Create a connection pool (reuse across Lambda invocations)
_connection_pool = None

def get_connection_pool():
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=os.environ['DATABASE_URL']  # Neon connection string
        )
    return _connection_pool

def get_db_connection():
    """Get a database connection from the pool"""
    pool = get_connection_pool()
    return pool.getconn()

def return_db_connection(conn):
    """Return connection to pool when done"""
    pool = get_connection_pool()
    pool.putconn(conn)
```

**Environment Variable:**
```bash
DATABASE_URL=postgresql://user:password@ep-cool-name-123456.us-east-2.aws.neon.tech/presently?sslmode=require
```

**Why connection pooling?**
- Lambda containers are reused across invocations
- Connection pool persists in Lambda's execution environment
- Reduces connection overhead (important for serverless)
- Neon handles the rest (no RDS Proxy needed)

### 4.5 Photo Upload Flow

1. Frontend requests presigned URL: `POST /photos/upload-url`
2. Lambda generates S3 presigned PUT URL
3. Frontend uploads directly to S3 using presigned URL
4. Frontend includes S3 URL when creating/updating wishlist item

---

## 5. CloudFormation Templates

### 5.1 Infrastructure Stack (Simplified - No VPC/RDS)

**File: `infrastructure/cloudformation/cognito-s3.yaml`**

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Presently Infrastructure - Cognito + S3 (Using Neon for Database)

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - prod

Resources:
  # Cognito User Pool
  UserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      UserPoolName: !Sub presently-${Environment}
      AutoVerifiedAttributes:
        - email
      UsernameAttributes:
        - email
      Schema:
        - Name: email
          Required: true
          Mutable: false
        - Name: name
          Required: true
          Mutable: true
      Policies:
        PasswordPolicy:
          MinimumLength: 8
          RequireUppercase: true
          RequireLowercase: true
          RequireNumbers: true
          RequireSymbols: true
      EmailConfiguration:
        EmailSendingAccount: COGNITO_DEFAULT  # Or use SES for custom domain

  UserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      UserPoolId: !Ref UserPool
      ClientName: !Sub presently-web-${Environment}
      GenerateSecret: false
      ExplicitAuthFlows:
        - ALLOW_USER_PASSWORD_AUTH
        - ALLOW_REFRESH_TOKEN_AUTH
      PreventUserExistenceErrors: ENABLED
      TokenValidityUnits:
        AccessToken: hours
        IdToken: hours
        RefreshToken: days
      AccessTokenValidity: 1
      IdTokenValidity: 1
      RefreshTokenValidity: 30

  # S3 Bucket for Photos
  PhotosBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub presently-photos-${Environment}
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      CorsConfiguration:
        CorsRules:
          - AllowedOrigins:
              - '*'  # Restrict to your domain in production
            AllowedMethods:
              - PUT
              - GET
              - HEAD
            AllowedHeaders:
              - '*'
            MaxAge: 3000

  # CloudFront Distribution for Photos (Optional but recommended)
  PhotosCDN:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Enabled: true
        Comment: !Sub Presently Photos CDN - ${Environment}
        Origins:
          - Id: S3Origin
            DomainName: !GetAtt PhotosBucket.RegionalDomainName
            S3OriginConfig:
              OriginAccessIdentity: !Sub origin-access-identity/cloudfront/${CloudFrontOAI}
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          AllowedMethods:
            - GET
            - HEAD
          CachedMethods:
            - GET
            - HEAD
          ForwardedValues:
            QueryString: false
            Cookies:
              Forward: none
          Compress: true
          DefaultTTL: 86400  # 1 day
          MaxTTL: 31536000   # 1 year
          MinTTL: 0
        PriceClass: PriceClass_100  # Use only North America and Europe
        ViewerCertificate:
          CloudFrontDefaultCertificate: true

  CloudFrontOAI:
    Type: AWS::CloudFront::CloudFrontOriginAccessIdentity
    Properties:
      CloudFrontOriginAccessIdentityConfig:
        Comment: !Sub OAI for presently-photos-${Environment}

  PhotosBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref PhotosBucket
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity ${CloudFrontOAI}
            Action: s3:GetObject
            Resource: !Sub ${PhotosBucket.Arn}/*

  # Lambda Execution Role
  LambdaRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub presently-lambda-role-${Environment}
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: LambdaS3Access
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:PutObject
                  - s3:GetObject
                  - s3:DeleteObject
                Resource: !Sub '${PhotosBucket.Arn}/*'
              - Effect: Allow
                Action:
                  - s3:ListBucket
                Resource: !GetAtt PhotosBucket.Arn

Outputs:
  UserPoolId:
    Description: Cognito User Pool ID
    Value: !Ref UserPool
    Export:
      Name: !Sub ${Environment}-UserPoolId

  UserPoolClientId:
    Description: Cognito User Pool Client ID
    Value: !Ref UserPoolClient
    Export:
      Name: !Sub ${Environment}-UserPoolClientId

  UserPoolArn:
    Description: Cognito User Pool ARN
    Value: !GetAtt UserPool.Arn
    Export:
      Name: !Sub ${Environment}-UserPoolArn

  PhotosBucketName:
    Description: S3 Bucket for Photos
    Value: !Ref PhotosBucket
    Export:
      Name: !Sub ${Environment}-PhotosBucket

  PhotosCDNDomain:
    Description: CloudFront CDN Domain for Photos
    Value: !GetAtt PhotosCDN.DomainName
    Export:
      Name: !Sub ${Environment}-PhotosCDN

  LambdaRoleArn:
    Description: Lambda Execution Role ARN
    Value: !GetAtt LambdaRole.Arn
    Export:
      Name: !Sub ${Environment}-LambdaRole
```

**Deploy Command:**
```bash
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/cognito-s3.yaml \
  --stack-name presently-infra-prod \
  --parameter-overrides Environment=prod \
  --capabilities CAPABILITY_NAMED_IAM
```

### 5.2 Lambda Deployment

Use **AWS SAM** or **Serverless Framework** for Lambda deployment:

**File: `backend/lambda/template.yaml` (SAM)**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Presently Lambda Functions

Parameters:
  Environment:
    Type: String
    Default: dev
  NeonDatabaseURL:
    Type: String
    Description: Neon Postgres connection string
    NoEcho: true

Globals:
  Function:
    Runtime: python3.11
    Timeout: 30
    MemorySize: 512
    Environment:
      Variables:
        DATABASE_URL: !Ref NeonDatabaseURL  # Neon connection string
        PHOTOS_BUCKET: !ImportValue !Sub ${Environment}-PhotosBucket
        PHOTOS_CDN: !ImportValue !Sub ${Environment}-PhotosCDN
        COGNITO_USER_POOL_ID: !ImportValue !Sub ${Environment}-UserPoolId
    Layers:
      - !Ref DependenciesLayer

Resources:
  # Shared Lambda Layer (psycopg2, etc.)
  DependenciesLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: !Sub presently-dependencies-${Environment}
      Description: Python dependencies (psycopg2, requests)
      ContentUri: dependencies/
      CompatibleRuntimes:
        - python3.11

  # API Gateway with Cognito Authorizer
  ApiGateway:
    Type: AWS::Serverless::Api
    Properties:
      Name: !Sub presently-api-${Environment}
      StageName: prod
      Cors:
        AllowMethods: "'GET, POST, PUT, DELETE, OPTIONS'"
        AllowHeaders: "'Content-Type, Authorization'"
        AllowOrigin: "'*'"  # Restrict in production
      Auth:
        DefaultAuthorizer: CognitoAuthorizer
        Authorizers:
          CognitoAuthorizer:
            UserPoolArn: !ImportValue !Sub ${Environment}-UserPoolArn

  # Groups Functions
  GroupsFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./
      Handler: handlers.groups.handler
      Role: !ImportValue !Sub ${Environment}-LambdaRole
      Events:
        GetGroups:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /groups
            Method: GET
        CreateGroup:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /groups
            Method: POST
        GetGroup:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /groups/{groupId}
            Method: GET
        UpdateGroup:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /groups/{groupId}
            Method: PUT
        DeleteGroup:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /groups/{groupId}
            Method: DELETE

  # Wishlist Functions
  WishlistFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./
      Handler: handlers.wishlist.handler
      Role: !ImportValue !Sub ${Environment}-LambdaRole
      Events:
        GetWishlist:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /wishlist
            Method: GET
        CreateItem:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /wishlist
            Method: POST

  # Purchases Function
  PurchasesFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./
      Handler: handlers.purchases.handler
      Role: !ImportValue !Sub ${Environment}-LambdaRole
      Events:
        ClaimItem:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /purchases
            Method: POST

  # Photos Function
  PhotosFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./
      Handler: handlers.photos.handler
      Role: !ImportValue !Sub ${Environment}-LambdaRole
      Events:
        UploadPhoto:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /photos/upload
            Method: POST

  # Invitations Function
  InvitationsFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./
      Handler: handlers.invitations.handler
      Role: !ImportValue !Sub ${Environment}-LambdaRole
      Events:
        GetInvitation:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /invitations/{token}
            Method: GET
            Auth:
              Authorizer: NONE  # Public endpoint
        AcceptInvitation:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /invitations/{token}/accept
            Method: POST

Outputs:
  ApiUrl:
    Description: API Gateway URL
    Value: !Sub https://${ApiGateway}.execute-api.${AWS::Region}.amazonaws.com/prod
    Export:
      Name: !Sub ${Environment}-ApiUrl
```

**Deploy Command:**
```bash
cd backend/lambda
sam build
sam deploy \
  --stack-name presently-lambda-prod \
  --parameter-overrides \
    Environment=prod \
    NeonDatabaseURL="postgresql://user:pass@ep-xxxx.aws.neon.tech/presently?sslmode=require" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3
```

---

## 6. Frontend Architecture

### 6.1 Next.js Project Structure

```
presently-frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                    # Landing page
│   ├── auth/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── dashboard/
│   │   ├── page.tsx
│   │   ├── groups/
│   │   │   ├── page.tsx
│   │   │   ├── new/page.tsx
│   │   │   └── [id]/
│   │   │       ├── page.tsx
│   │   │       └── manage/page.tsx
│   │   └── wishlists/
│   │       ├── page.tsx
│   │       ├── new/page.tsx
│   │       └── [id]/edit/page.tsx
│   └── invite/[token]/page.tsx
├── components/
│   ├── ui/                         # Reusable UI components
│   ├── DashboardNav.tsx
│   ├── WishlistItemCard.tsx
│   ├── AddMemberForm.tsx
│   └── ...
├── lib/
│   ├── api.ts                      # API client (Axios/Fetch)
│   ├── auth.ts                     # Cognito auth helpers
│   └── hooks/
│       ├── useAuth.ts
│       ├── useGroups.ts
│       └── useWishlist.ts
├── styles/
│   └── globals.css
├── tailwind.config.ts
└── next.config.js
```

### 6.2 API Client

**File: `lib/api.ts`**
```typescript
import axios from 'axios'
import { getAuthToken } from './auth'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
})

// Add auth token to all requests
api.interceptors.request.use(async (config) => {
  const token = await getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// API methods
export const apiClient = {
  // Profile
  getProfile: () => api.get('/profile'),
  updateProfile: (data: any) => api.put('/profile', data),

  // Groups
  getGroups: () => api.get('/groups'),
  createGroup: (data: any) => api.post('/groups', data),
  getGroup: (id: string) => api.get(`/groups/${id}`),
  updateGroup: (id: string, data: any) => api.put(`/groups/${id}`, data),
  deleteGroup: (id: string) => api.delete(`/groups/${id}`),
  inviteMember: (groupId: string, email: string) =>
    api.post(`/groups/${groupId}/members`, { email }),
  removeMember: (groupId: string, userId: string) =>
    api.delete(`/groups/${groupId}/members/${userId}`),

  // Wishlist
  getWishlist: () => api.get('/wishlist'),
  createItem: (data: any) => api.post('/wishlist', data),
  updateItem: (id: string, data: any) => api.put(`/wishlist/${id}`, data),
  deleteItem: (id: string) => api.delete(`/wishlist/${id}`),
  reorderItems: (items: any[]) => api.put('/wishlist/reorder', { items }),

  // Purchases
  claimItem: (itemId: string, groupId: string) =>
    api.post('/purchases', { itemId, groupId }),
  unclaimItem: (itemId: string, groupId: string) =>
    api.delete(`/purchases/${itemId}/${groupId}`),

  // Invitations
  getInvitation: (token: string) => api.get(`/invitations/${token}`),
  acceptInvitation: (token: string) => api.post(`/invitations/${token}/accept`),

  // Photos
  uploadPhoto: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/photos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
}
```

### 6.3 Cognito Auth

**File: `lib/auth.ts`**
```typescript
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
} from 'amazon-cognito-identity-js'

const userPool = new CognitoUserPool({
  UserPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
  ClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
})

export async function signUp(email: string, password: string, name: string) {
  return new Promise((resolve, reject) => {
    userPool.signUp(
      email,
      password,
      [{ Name: 'name', Value: name }],
      [],
      (err, result) => {
        if (err) reject(err)
        else resolve(result)
      }
    )
  })
}

export async function signIn(email: string, password: string) {
  const user = new CognitoUser({ Username: email, Pool: userPool })
  const authDetails = new AuthenticationDetails({ Username: email, Password: password })

  return new Promise((resolve, reject) => {
    user.authenticateUser(authDetails, {
      onSuccess: resolve,
      onFailure: reject,
    })
  })
}

export async function getAuthToken(): Promise<string | null> {
  const user = userPool.getCurrentUser()
  if (!user) return null

  return new Promise((resolve) => {
    user.getSession((err: any, session: any) => {
      if (err || !session.isValid()) resolve(null)
      else resolve(session.getIdToken().getJwtToken())
    })
  })
}

export function signOut() {
  const user = userPool.getCurrentUser()
  if (user) user.signOut()
}

export function getCurrentUser() {
  return userPool.getCurrentUser()
}
```

---

## 7. Design System & Styling

### 7.1 Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: 'class',
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors if needed
      },
    },
  },
  plugins: [],
};
export default config;
```

### 7.2 Design Tokens

**Colors:**
- Primary: `blue-600` / `blue-400` (dark mode)
- Success: `green-600` / `green-400`
- Error: `red-600` / `red-400`
- Background: `gray-50` / `gray-900`
- Cards: `white` / `gray-800`
- Text: `gray-900` / `gray-100`
- Secondary text: `gray-600` / `gray-300`

**Typography:**
- Headings: `font-bold`
  - H1: `text-3xl`
  - H2: `text-2xl`
  - H3: `text-xl`
- Body: Default
- Small: `text-sm`
- Tiny: `text-xs`

**Spacing:**
- Page padding: `py-6 px-4 sm:px-6 lg:px-8`
- Card padding: `p-6`
- Section spacing: `space-y-4` or `space-y-6`
- Button padding: `px-4 py-2` (small), `px-6 py-3` (medium)

**Borders & Shadows:**
- Cards: `rounded-lg shadow`
- Buttons: `rounded-lg`
- Input fields: `rounded-md border border-gray-300 dark:border-gray-600`
- Focus rings: `focus:outline-none focus:ring-2 focus:ring-blue-500`

**Buttons:**
```tsx
// Primary
className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"

// Secondary
className="px-6 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-lg font-medium"

// Danger
className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium"

// Disabled
className="... disabled:opacity-50 disabled:cursor-not-allowed"
```

**Cards:**
```tsx
className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
```

**Form Inputs:**
```tsx
className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
```

### 7.3 Dark Mode Implementation

**Theme Provider:**
```tsx
// components/ThemeProvider.tsx
'use client'
import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext({ theme: 'light', toggleTheme: () => {} })

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const saved = localStorage.getItem('theme')
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    setTheme(saved === 'dark' || (!saved && prefersDark) ? 'dark' : 'light')
  }, [])

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(theme === 'light' ? 'dark' : 'light')

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
```

### 7.4 Component Patterns

**Wishlist Item Card:**
```tsx
<div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
  {/* Photo */}
  {photoUrl && (
    <img
      src={photoUrl}
      alt={name}
      className="w-full h-48 object-cover rounded-lg mb-4"
    />
  )}

  {/* Item Name */}
  <h3 className="text-lg font-semibold mb-2">{name}</h3>

  {/* Description */}
  {description && (
    <p className="text-gray-600 dark:text-gray-300 text-sm mb-3">
      {description}
    </p>
  )}

  {/* Price & URL */}
  <div className="flex justify-between items-center mb-4">
    {price && (
      <span className="text-gray-900 dark:text-gray-100 font-medium">
        ${price}
      </span>
    )}
    {url && (
      <a
        href={url}
        target="_blank"
        className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
      >
        View →
      </a>
    )}
  </div>

  {/* Purchase Button (only if not owner) */}
  {!isOwner && (
    <button className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium">
      {isPurchased ? 'Purchased ✓' : 'Mark as Purchased'}
    </button>
  )}
</div>
```

**Collapsible Wishlist Section:**
```tsx
<div className="bg-white dark:bg-gray-800 rounded-lg shadow">
  {/* Header - clickable to expand/collapse */}
  <button
    onClick={toggle}
    className="w-full p-6 flex justify-between items-center hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
  >
    <h2 className="text-xl font-semibold">{memberName}'s Wishlist</h2>
    <span className="text-2xl">{isOpen ? '−' : '+'}</span>
  </button>

  {/* Content - hidden when collapsed */}
  {isOpen && (
    <div className="p-6 pt-0 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map(item => <WishlistItemCard key={item.id} {...item} />)}
    </div>
  )}
</div>
```

**Dashboard Navigation:**
```tsx
<nav className="bg-white dark:bg-gray-800 shadow">
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div className="flex justify-between h-16">
      <div className="flex items-center">
        <h1 className="text-2xl font-bold">Presently</h1>
      </div>

      <div className="flex items-center space-x-4">
        <Link
          href="/dashboard"
          className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
        >
          Dashboard
        </Link>
        <Link
          href="/dashboard/groups"
          className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
        >
          Groups
        </Link>
        <Link
          href="/dashboard/wishlists"
          className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
        >
          My Wishlists
        </Link>

        <ThemeToggle />

        <button
          onClick={signOut}
          className="px-4 py-2 text-red-600 dark:text-red-400 hover:underline"
        >
          Sign Out
        </button>
      </div>
    </div>
  </div>
</nav>
```

---

## 8. Migration Strategy

### 8.1 Data Migration

**Export from Supabase:**
1. Use `pg_dump` to export data:
   ```bash
   pg_dump -h db.xxx.supabase.co -U postgres -d postgres \
     --data-only --table=profiles --table=groups \
     --table=group_memberships --table=wishlist_items \
     --table=item_group_assignments --table=purchases \
     --table=group_invitations > data.sql
   ```

2. Transform user IDs from Supabase Auth UUIDs to Cognito User Subs
3. Import to RDS Postgres:
   ```bash
   psql -h <rds-endpoint> -U postgres -d presently < data.sql
   ```

**User Migration:**
- **Option 1**: Ask users to re-register (simplest, but loses data association)
- **Option 2**: Use Cognito User Import (create CSV from Supabase users)
- **Option 3**: Implement password migration trigger (users re-auth once)

### 8.2 Phased Rollout

**Phase 1: Infrastructure Setup (Week 1)**
- Deploy CloudFormation stacks
- Set up Cognito User Pool
- Create RDS database and run migrations
- Deploy Lambda functions
- Configure API Gateway

**Phase 2: Frontend Migration (Week 2)**
- Build new Next.js frontend
- Integrate with Cognito auth
- Connect to Lambda APIs
- Test all user flows

**Phase 3: Data Migration (Week 3)**
- Export data from Supabase
- Import to RDS
- Migrate users to Cognito
- Test data integrity

**Phase 4: Testing & Deployment (Week 4)**
- End-to-end testing
- Performance testing
- Deploy to production
- Monitor logs and metrics

**Phase 5: Deprecate Supabase (Week 5)**
- Redirect old domain to new app
- Shut down Supabase project
- Archive backups

---

## 9. Deployment Guide

### 9.1 Prerequisites

1. **AWS Account** with admin access
2. **AWS CLI** configured
3. **SAM CLI** installed
4. **Vercel Account** for frontend hosting

### 9.2 Deploy Infrastructure

```bash
# Step 1: Create SSM parameters for secrets
aws ssm put-parameter \
  --name /presently/prod/db/username \
  --value "postgres" \
  --type String

aws ssm put-parameter \
  --name /presently/prod/db/password \
  --value "YourSecurePassword123!" \
  --type SecureString

# Step 2: Deploy infrastructure
aws cloudformation deploy \
  --template-file infrastructure.yaml \
  --stack-name presently-infra-prod \
  --parameter-overrides Environment=prod \
  --capabilities CAPABILITY_IAM

# Step 3: Run database migrations
# Get RDS endpoint from stack outputs
DB_HOST=$(aws cloudformation describe-stacks \
  --stack-name presently-infra-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DBProxyEndpoint`].OutputValue' \
  --output text)

# Run schema SQL
psql -h $DB_HOST -U postgres -d presently < schema.sql
```

### 9.3 Deploy Lambda Functions

```bash
# Build and deploy with SAM
cd lambda/
sam build
sam deploy \
  --template-file template.yaml \
  --stack-name presently-lambda-prod \
  --parameter-overrides Environment=prod \
  --capabilities CAPABILITY_IAM \
  --resolve-s3
```

### 9.4 Deploy Frontend to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd presently-frontend/
vercel --prod

# Set environment variables in Vercel dashboard:
# - NEXT_PUBLIC_API_URL
# - NEXT_PUBLIC_COGNITO_USER_POOL_ID
# - NEXT_PUBLIC_COGNITO_CLIENT_ID
```

---

## 10. Cost Estimate (FREE TIER OPTIMIZED)

### Free Tier Usage (Personal/Family App)

**Monthly Costs for < 50 users, < 1M requests/month:**

| Service | Free Tier Limit | Usage | Cost |
|---------|----------------|-------|------|
| **Vercel** | Unlimited | Hosting | **$0** ✅ |
| **Cognito** | 50,000 MAU | ~10-50 users | **$0** ✅ |
| **API Gateway** | 1M requests/month | ~30k requests/day | **$0** ✅ |
| **Lambda** | 1M requests + 400k GB-sec | ~30k requests/day | **$0** ✅ |
| **Neon Postgres** | 0.5GB storage | ~5,000 wishlist items | **$0** ✅ |
| **S3 Storage** | 5GB free | 10GB photos | **~$0.12** |
| **CloudFront** | 1TB free | 10GB transfer | **$0** ✅ |
| **TOTAL** | | | **~$0-1/month** 🎉 |

### When You Start Paying

**Scaling to 100 users (~3M requests/month, 50GB photos):**

| Service | Cost |
|---------|------|
| Vercel | $0 (still free) |
| Cognito | $0 (still free < 50k MAU) |
| API Gateway | $7.00 (2M extra requests × $3.50/M) |
| Lambda | $0.40 (2M extra requests × $0.20/M) |
| Neon Postgres | $0 (still < 0.5GB) |
| S3 Storage | $1.15 (50GB × $0.023/GB) |
| CloudFront | $4.25 (50GB × $0.085/GB) |
| **TOTAL** | **~$13/month** |

### Cost Comparison: Free Tier vs Previous RDS Plan

| Architecture | Monthly Cost |
|--------------|--------------|
| **Neon + Free Tier** (this plan) | **$0-1** ✅ |
| RDS + RDS Proxy (original) | ~$38 |
| **Savings** | **~$37/month** 💰 |

### Free Tier Summary

✅ **Stays FREE as long as:**
- < 50,000 monthly active users
- < 1 million API requests/month (~33k per day)
- < 0.5GB database storage
- < 5GB photo storage

🚀 **Even with growth to 100 users:**
- Still only ~$13/month
- Far cheaper than RDS ($38+/month)
- No VPC complexity
- No RLS headaches

---

## 11. Testing Strategy

### 11.1 Backend Tests

```python
# tests/test_groups.py
import pytest
from handlers.groups import get_groups, create_group

def test_get_groups():
    user_id = "test-user-id"
    groups = get_groups(user_id)
    assert isinstance(groups, list)

def test_create_group():
    user_id = "test-user-id"
    data = {"name": "Test Group", "description": "A test group"}
    result = create_group(user_id, data)
    assert result['id']
    assert result['name'] == "Test Group"
```

### 11.2 Frontend Tests

```typescript
// __tests__/auth.test.ts
import { signIn, signUp } from '@/lib/auth'

describe('Authentication', () => {
  it('should sign up a new user', async () => {
    const result = await signUp('test@example.com', 'Password123!', 'Test User')
    expect(result).toBeDefined()
  })

  it('should sign in existing user', async () => {
    const result = await signIn('test@example.com', 'Password123!')
    expect(result.idToken).toBeDefined()
  })
})
```

### 11.3 Integration Tests

Use Postman or REST Client to test API endpoints end-to-end.

---

## 12. Monitoring & Logging

### 12.1 CloudWatch Logs

All Lambda functions automatically log to CloudWatch:
- Request/response logs
- Error traces
- Custom application logs

### 12.2 CloudWatch Metrics

Monitor:
- Lambda invocation count
- Lambda errors
- API Gateway 4xx/5xx errors
- RDS CPU/connections

### 12.3 Alarms

Set up SNS alarms for:
- Lambda error rate > 1%
- API Gateway 5xx errors
- RDS CPU > 80%
- RDS connections > 90% of max

---

## 13. Security Best Practices

1. **Secrets Management**: Use AWS Systems Manager Parameter Store (never hardcode)
2. **API Authorization**: All endpoints require Cognito JWT (except public invite page)
3. **Database Security**: RDS in private subnet, only accessible via RDS Proxy
4. **S3 Security**: Bucket policies restrict public access, use presigned URLs
5. **HTTPS Only**: Enforce HTTPS at API Gateway and CloudFront
6. **Input Validation**: Validate all user inputs in Lambda functions
7. **SQL Injection Prevention**: Use parameterized queries (psycopg2)
8. **CORS**: Restrict to frontend domain only

---

## 14. Future Enhancements

1. **Real-time Updates**: Use WebSocket API for live purchase notifications
2. **Email Notifications**: SES templates for invitation reminders, purchase alerts
3. **Mobile App**: React Native with same Lambda backend
4. **Analytics**: Track most-wanted items, purchase patterns
5. **AI Recommendations**: Suggest gifts based on past wishlists
6. **Price Tracking**: Monitor price drops for wishlist URLs
7. **Group Budgets**: Track spending per group/person
8. **Gift Exchanges**: Secret Santa assignment logic

---

## 15. Summary

This plan provides everything needed to rebuild Presently on AWS infrastructure:

✅ **Complete database schema** with all tables and relationships
✅ **Full API specification** with request/response formats
✅ **AWS architecture** with CloudFormation templates
✅ **Lambda function structure** with Python examples
✅ **Frontend architecture** with Next.js + Cognito integration
✅ **Design system export** with Tailwind patterns
✅ **Migration strategy** from Supabase to AWS
✅ **Deployment guide** with step-by-step instructions
✅ **Cost estimates** for realistic budgeting
✅ **Security and monitoring** best practices

**Next Steps:**
1. Review and approve this plan
2. Set up AWS account and permissions
3. Deploy infrastructure using CloudFormation
4. Build and deploy Lambda functions
5. Build new Next.js frontend
6. Migrate data from Supabase
7. Test thoroughly
8. Deploy to production

This architecture is production-ready, scalable, and cost-effective for a family/friends wishlist application.
