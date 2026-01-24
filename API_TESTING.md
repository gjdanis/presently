# API Testing Guide

Scripts to test the Presently API endpoints.

## Prerequisites

- AWS CLI configured with credentials
- `jq` installed (`brew install jq` on macOS)
- API deployed to AWS (`make deploy-lambda ENV=dev`)
- Database migrations run (`make db-migrate`)

## Quick Start

### 1. Create a Test User

```bash
./create-test-user.sh dev test@example.com TestPass123! "John Doe"
```

This will:
- Create user in Cognito
- Auto-confirm the email (in dev environment)
- **Automatically create the profile in the database via Cognito trigger**
- Get an authentication token

No manual database steps needed! The Cognito Post-Confirmation trigger automatically creates the profile.

### 2. Get Authentication Token

If you already have a user:

```bash
./get-token.sh dev test@example.com TestPass123!
```

Copy the token and export it:

```bash
export JWT_TOKEN='eyJraWQiOi...'
```

### 3. Test the API

```bash
./test-api.sh dev
```

This will run through all the main endpoints:
- Create/read/update/delete profile
- Create/read/update/delete groups
- Create/read/update/delete wishlist items
- Test public endpoints (invitations)

## Manual Testing

### Profile Endpoints

**Get Profile:**
```bash
curl -X GET \
  -H "Authorization: Bearer $JWT_TOKEN" \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/profile
```

**Update Profile:**
```bash
curl -X PUT \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Name"}' \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/profile
```

### Group Endpoints

**Create Group:**
```bash
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Family",
    "description": "Family gift exchange"
  }' \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/groups
```

**Get Groups:**
```bash
curl -X GET \
  -H "Authorization: Bearer $JWT_TOKEN" \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/groups
```

**Get Group Details:**
```bash
curl -X GET \
  -H "Authorization: Bearer $JWT_TOKEN" \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/groups/{group-id}
```

**Update Group (admin only):**
```bash
curl -X PUT \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}' \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/groups/{group-id}
```

**Delete Group (admin only):**
```bash
curl -X DELETE \
  -H "Authorization: Bearer $JWT_TOKEN" \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/groups/{group-id}
```

### Wishlist Endpoints

**Create Wishlist Item:**
```bash
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Noise Cancelling Headphones",
    "description": "Sony WH-1000XM5",
    "url": "https://amazon.com/...",
    "price": 299.99,
    "groupIds": ["group-id-1", "group-id-2"]
  }' \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/wishlist
```

**Get Wishlist:**
```bash
curl -X GET \
  -H "Authorization: Bearer $JWT_TOKEN" \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/wishlist
```

**Update Item:**
```bash
curl -X PUT \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"price": 279.99}' \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/wishlist/{item-id}
```

**Reorder Items:**
```bash
curl -X PUT \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"id": "item-1", "rank": 0},
      {"id": "item-2", "rank": 1},
      {"id": "item-3", "rank": 2}
    ]
  }' \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/wishlist/reorder
```

### Purchase Endpoints

**Claim Item (mark as purchased):**
```bash
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "itemId": "item-id",
    "groupId": "group-id"
  }' \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/purchases
```

**Unclaim Item:**
```bash
curl -X DELETE \
  -H "Authorization: Bearer $JWT_TOKEN" \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/purchases/{item-id}/{group-id}
```

### Invitation Endpoints

**Send Invitation:**
```bash
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "friend@example.com"}' \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/groups/{group-id}/members
```

**Get Invitation (public - no auth):**
```bash
curl -X GET \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/invitations/{token}
```

**Accept Invitation:**
```bash
curl -X POST \
  -H "Authorization: Bearer $JWT_TOKEN" \
  https://r5odhqk4hl.execute-api.us-east-2.amazonaws.com/dev/invitations/{token}/accept
```

## Troubleshooting

### "User is not confirmed"
Run:
```bash
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id $(aws ssm get-parameter --name /dev/UserPoolId --query 'Parameter.Value' --output text) \
  --username test@example.com
```

### "Profile not found"
This shouldn't happen if the Cognito triggers are configured correctly. The profile should be created automatically.

Check if triggers are configured:
```bash
make configure-cognito-triggers ENV=dev
```

Or manually create the profile:
```sql
INSERT INTO profiles (id, email, name)
VALUES ('user-sub-from-cognito', 'test@example.com', 'John Doe');
```

### "Invalid token"
Your token might have expired (1 hour). Get a new one:
```bash
./get-token.sh dev test@example.com TestPass123!
export JWT_TOKEN='new-token-here'
```

### Check CloudWatch Logs
```bash
# List log groups
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/presently

# Tail logs for a function
aws logs tail /aws/lambda/presently-lambda-dev-ProfileFunction --follow
```

## Environment Variables

For production testing, change `dev` to `prod`:

```bash
./create-test-user.sh prod test@example.com TestPass123! "John Doe"
./get-token.sh prod test@example.com TestPass123!
./test-api.sh prod
```

## Next Steps

Once the API is working:
1. Build the frontend (Next.js)
2. Integrate Cognito authentication in the UI
3. Connect frontend to these API endpoints
4. Deploy frontend to Vercel
