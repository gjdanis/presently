# Presently – Project Context

Presently is a **multi-group wishlist web app** for families and friends.

Users:
- Create wishlists with items
- Belong to multiple groups
- View other members’ wishlists
- Secretly mark others’ items as purchased (owners must NOT see purchase status)

---

## Tech Stack (Important)

**Frontend**
- Next.js (App Router)
- TypeScript
- Tailwind CSS
- Hosted on Vercel

**Backend**
- AWS Lambda (Python 3.11)
- API Gateway (REST)
- Auth via AWS Cognito (JWT)
- Database: Neon Postgres (serverless)
- Storage: S3 (photos via presigned URLs)

**Key Constraints**
- Optimize for AWS free tier
- No Supabase
- No RDS, no VPC
- Authorization handled in Lambda code (not DB RLS)

---

## Core Domain Rules (Critical)

### Groups & Membership
- Users can only access groups they belong to
- Groups have admins and members
- Only admins can manage members or invitations

### Wishlist Items
- Users can only edit/delete their own items
- Items can be shared with multiple groups
- Items are ordered via a numeric `rank`

### Purchases (Privacy Rule – VERY IMPORTANT)
- Item owners **must never see** purchase status
- Other group members **can** see purchases
- Only one purchase per item per group

### Invitations
- Invitations use shareable links with multi-use tokens
- Optional: max uses limit, expiration time
- Users may accept invites before or after registering
- Accepting an invite auto-adds the user to the group

---

## Database Model (High-Level)

Main tables:
- `profiles` (Cognito users)
- `groups`
- `group_memberships`
- `wishlist_items`
- `item_group_assignments`
- `purchases`
- `group_invitations`
- `invitation_acceptances` (tracks multi-use invite usage)

Postgres is the source of truth.  
No soft deletes unless explicitly requested.

---

## API Conventions

- REST-style endpoints
- JWT required for all private routes
- Consistent JSON responses
- Authorization always checked server-side
- Never trust frontend role or ownership claims

---

## Lambda Structure

- FastAPI app with Mangum adapter for Lambda
- Organized by layer:
  - `routers/` - API endpoints (groups.py, wishlist.py, etc.)
  - `services/` - Business logic
  - `repositories/` - Data access
- Shared utilities:
  - Auth (JWT verification)
  - DB access
  - Response helpers
  - Validation helpers

Prefer **clear, explicit code** over abstractions.

---

## Frontend Guidelines

- App Router (`/app`)
- Server Components by default
- Client Components only when needed
- API calls via a shared client
- Cognito handles auth; frontend stores JWT only
- UI must respect purchase privacy rules

---

## What NOT to Do

- Do NOT reintroduce Supabase
- Do NOT use database-level RLS
- Do NOT expose purchase info to item owners
- Do NOT add unnecessary services or frameworks
- Do NOT optimize prematurely

---

## Priorities

1. Correctness > cleverness
2. Privacy rules enforced everywhere
3. Simple, readable code
4. Low cost, low ops
