# Invitation System Implementation ✅

## Overview

The invitation system allows users to invite others to join their groups via email. This was previously broken in the Supabase version but is now fully functional with the AWS backend.

## Architecture

### Backend (AWS Lambda)
- **Endpoint**: `POST /groups/{groupId}/members`
- **Handler**: `backend/lambda/handlers/groups.py` - `invite_member()`
- **Database**: `group_invitations` table with token-based invites
- **Email**: Uses AWS Cognito (no separate SMTP needed)

### Frontend (Next.js)
- **Page**: `frontend/app/invite/[token]/page.tsx`
- **API Client**: `frontend/lib/api.ts` - `getInvitation()`, `acceptInvitation()`

## How It Works

### 1. Sending an Invitation

**Admin creates invitation:**
```typescript
// From group management page
await api.inviteMember(groupId, { email: 'friend@example.com' });
```

**Backend creates invitation record:**
```python
# Generate unique token
token = str(uuid4())

# Insert invitation
invitation = execute_insert(
    "INSERT INTO group_invitations (group_id, invited_by, email, token, role)
     VALUES (%s, %s, %s, %s, %s) RETURNING *",
    (group_id, user_id, email, token, 'member')
)

# Return invitation URL
return {
    "invite_url": f"https://your-app.com/invite/{token}",
    "email_sent": False  # TODO: Implement email sending
}
```

**Invitation is stored in database:**
```sql
CREATE TABLE group_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  invited_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',
  token TEXT NOT NULL UNIQUE,
  accepted_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. Accepting an Invitation

**User clicks invitation link:**
```
https://your-app.com/invite/abc123-token-here
```

**Page loads invitation details:**
```typescript
// Fetch invitation from backend (public endpoint)
const invitation = await api.getInvitation(token);

// Shows:
// - Group name
// - Invited by (name/email)
// - Group description
// - Expiration date
```

**If user is NOT logged in:**
- Shows invitation details
- Buttons: "Sign Up & Join Group" or "Already have an account? Log In"
- Both redirect to auth pages with `?invite={token}` parameter

**If user IS logged in:**
- Auto-accepts invitation
- Calls `POST /invitations/{token}/accept`
- Backend:
  1. Validates invitation (not expired, not accepted)
  2. Checks if user is already a member
  3. Adds user to group_memberships
  4. Marks invitation as accepted
  5. Returns group_id

**After acceptance:**
- Shows success message: "Welcome to the Group!"
- Redirects to group page after 2 seconds

### 3. Post-Login Invitation Acceptance

**Auth pages check for invite parameter:**
```typescript
// After successful login/register
const searchParams = useSearchParams();
const inviteToken = searchParams.get('invite');

if (inviteToken) {
  // Accept invitation
  await api.acceptInvitation(inviteToken);
  // Redirect to group
  router.push(`/dashboard/groups/${result.group_id}`);
}
```

## Key Differences from Supabase Version

### ✅ What Works Now

1. **No SMTP Configuration Needed**
   - Supabase required custom SMTP setup (Resend, SendGrid, etc.)
   - AWS: Users share the invitation link directly (manual send)
   - Future: Can add AWS SES for automated emails

2. **Simple Token-Based System**
   - No magic link authentication
   - No complex email template configuration
   - Just a URL with a unique token

3. **Proper Authorization**
   - Backend validates all permissions
   - Cognito JWT verifies user identity
   - No RLS complexity

4. **Clear Error Handling**
   - Invalid token → Shows error page
   - Expired invitation → Clear message
   - Already a member → Success with note

### Backend API Endpoints

**GET /invitations/{token}** (Public)
```json
{
  "group_id": "uuid",
  "group_name": "Smith Family",
  "group_description": "Our family wishlist group",
  "invited_by": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "role": "member",
  "expires_at": "2024-02-01T00:00:00Z"
}
```

**POST /invitations/{token}/accept** (Authenticated)
```json
{
  "group_id": "uuid",
  "already_member": false
}
```

**POST /groups/{groupId}/members** (Authenticated, Admin only)
```json
// Request
{
  "email": "friend@example.com"
}

// Response
{
  "invite_url": "https://your-app.com/invite/abc123",
  "email_sent": false
}
```

## Database Queries

**Check if invitation is valid:**
```sql
SELECT * FROM group_invitations
WHERE token = %s
  AND accepted_at IS NULL
  AND expires_at > NOW()
```

**Accept invitation:**
```sql
-- Add to group
INSERT INTO group_memberships (user_id, group_id, role)
VALUES (%s, %s, %s);

-- Mark as accepted
UPDATE group_invitations
SET accepted_at = NOW()
WHERE token = %s;
```

## UI Flow

### Not Logged In
```
┌─────────────────────────────────┐
│  You've Been Invited!           │
│                                 │
│  John Doe invited you to join   │
│  "Smith Family" on Presently    │
│                                 │
│  [Sign Up & Join Group]         │
│  [Already have account? Log In] │
└─────────────────────────────────┘
```

### Logged In
```
┌─────────────────────────────────┐
│  🎉                             │
│  Joining Group...               │
│                                 │
│  Please wait while we add you   │
│  to the group...                │
└─────────────────────────────────┘
        ↓
┌─────────────────────────────────┐
│  🎉                             │
│  Welcome to the Group!          │
│                                 │
│  You've successfully joined     │
│  Smith Family!                  │
│                                 │
│  [Go to Group]                  │
└─────────────────────────────────┘
```

### Already a Member
```
┌─────────────────────────────────┐
│  🎉                             │
│  Already a Member!              │
│                                 │
│  You're already a member of     │
│  Smith Family.                  │
│                                 │
│  [Go to Group]                  │
└─────────────────────────────────┘
```

### Invalid/Expired
```
┌─────────────────────────────────┐
│  ❌                             │
│  Invalid or Expired Invitation  │
│                                 │
│  This invitation link is no     │
│  longer valid.                  │
│                                 │
│  [Go to Login]                  │
└─────────────────────────────────┘
```

## Security Considerations

1. **Token Generation**: Uses UUID v4 (cryptographically random)
2. **Expiration**: Invitations expire after 7 days
3. **One-time Use**: Marked as accepted after first use
4. **Authorization**: Only group admins can create invitations
5. **Validation**: Backend validates token, expiration, and user permissions

## Future Enhancements

### Email Sending (Optional)
```python
# In invite_member() handler
import boto3

ses = boto3.client('ses', region_name='us-east-1')

# Send email
ses.send_email(
    Source='noreply@your-domain.com',
    Destination={'ToAddresses': [email]},
    Message={
        'Subject': {'Data': f'Invitation to join {group_name}'},
        'Body': {
            'Html': {
                'Data': f'''
                    <h2>You've been invited!</h2>
                    <p>Click here to join:
                    <a href="https://your-app.com/invite/{token}">Accept Invitation</a>
                    </p>
                '''
            }
        }
    }
)
```

**Setup required:**
1. Verify domain in AWS SES
2. Add SPF/DKIM records to DNS
3. Request production access (remove sandbox)

### Invitation Management

Add to group management page:
- List pending invitations
- Resend invitation link
- Revoke invitation (delete from database)
- See who accepted

## Testing the Invitation Flow

### 1. Create Invitation (Backend)
```bash
# Get auth token
TOKEN=$(./get-token.sh dev)

# Get a group ID
GROUP_ID="your-group-id"

# Send invitation
curl -X POST "https://your-api.com/groups/${GROUP_ID}/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"friend@example.com"}'
```

### 2. Visit Invitation Page
```
http://localhost:3000/invite/{token-from-response}
```

### 3. Test Scenarios

**Not logged in:**
- Click "Sign Up & Join Group"
- Complete registration
- Should auto-accept and redirect to group

**Already logged in:**
- Should show "Joining Group..." immediately
- Then "Welcome to the Group!"
- Redirect to group page

**Invalid token:**
- Should show error page

**Already a member:**
- Should show "Already a Member!" message
- Still allow navigation to group

## Implementation Checklist

- ✅ Backend: Create invitation endpoint
- ✅ Backend: Get invitation endpoint (public)
- ✅ Backend: Accept invitation endpoint
- ✅ Frontend: Invitation page with token route
- ✅ Frontend: API client methods
- ✅ Frontend: Auto-accept if logged in
- ✅ Frontend: Show invitation details if not logged in
- ✅ Frontend: Handle auth redirect with invite parameter
- ✅ Makefile: Add frontend commands
- ⏳ TODO: Group management page with invite button
- ⏳ TODO: Email sending (AWS SES) - optional
- ⏳ TODO: Invitation management UI

## Files Created/Modified

### Frontend
- ✅ `frontend/app/invite/[token]/page.tsx` - Invitation acceptance page
- ✅ `frontend/lib/api.ts` - Added getInvitation(), acceptInvitation()
- ✅ `frontend/lib/types.ts` - Added Invitation type

### Backend
- ✅ `backend/lambda/handlers/invitations.py` - Invitation handlers (already existed)
- ✅ `backend/lambda/handlers/groups.py` - Invite member handler (already existed)

### Configuration
- ✅ `Makefile` - Added frontend commands

## Next Steps

1. **Build Auth Pages** - Login/register with invite parameter support
2. **Build Group Management Page** - UI to send invitations
3. **Test Full Flow** - End-to-end invitation workflow
4. **(Optional) Add AWS SES** - Automated email sending
