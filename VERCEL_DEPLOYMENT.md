# Presently - Vercel Deployment Guide

## Prerequisites

1. [Vercel Account](https://vercel.com/signup) (free)
2. GitHub repository (optional, but recommended for auto-deployments)

## Quick Start: Deploy via Vercel CLI

### 1. Install Vercel CLI
```bash
npm install -g vercel
```

### 2. Navigate to frontend directory
```bash
cd frontend
```

### 3. Login to Vercel
```bash
vercel login
```

### 4. Deploy
```bash
vercel --prod
```

### 5. Set Environment Variables

After deployment, add these environment variables (from `frontend/.env.vercel.example`):

```bash
vercel env add NEXT_PUBLIC_API_URL production
# Paste: https://m7oou2xhf0.execute-api.us-east-1.amazonaws.com/dev

vercel env add NEXT_PUBLIC_COGNITO_USER_POOL_ID production
# Paste: us-east-1_j7vCYcPVp

vercel env add NEXT_PUBLIC_COGNITO_CLIENT_ID production
# Paste: 6nic4kigvu9mbekahh13nsclpu

vercel env add NEXT_PUBLIC_COGNITO_REGION production
# Paste: us-east-1

vercel env add NEXT_PUBLIC_CDN_URL production
# Paste: https://d3h1arh9hpah7a.cloudfront.net
```

### 6. Redeploy with environment variables
```bash
vercel --prod
```

### 7. Note Your Vercel URL
Example: `https://presently-abc123.vercel.app`

---

## After Deployment: Update Backend

### Update Lambda FRONTEND_URL

```bash
# Add your Vercel URL to .env.development
echo "VERCEL_URL=https://your-app.vercel.app" >> .env.development

# Redeploy Lambda with new frontend URL
export $(cat .env.development | xargs)
export FRONTEND_URL=$VERCEL_URL
make deploy-lambda ENV=dev
```

Or manually edit `backend/lambda/template.yaml` and change:
```yaml
FRONTEND_URL: https://your-app.vercel.app
```

---

## Test the Full Flow

1. **Send an invitation** from your app
2. **Check the email** - link should now point to `https://your-app.vercel.app/invite/...`
3. **Click the link** - should load the invitation page
4. **Accept invitation** - should successfully join the group

---

## Production Checklist

- [ ] Vercel deployment succeeds
- [ ] All environment variables set
- [ ] Can log in/register users
- [ ] Can create/manage groups
- [ ] Invitation emails have correct Vercel URL
- [ ] Can accept invitations
- [ ] Can create wishlist items with photos
- [ ] Dark mode works
- [ ] Mobile responsive

---

## Next Steps

1. **Request AWS SES Production Access** (removes sandbox email restrictions)
   - Go to: https://console.aws.amazon.com/ses/home?region=us-east-1#/account
   - Click "Request production access"
   - Fill out form (usually approved in 24 hours)

2. **Optional: Add Custom Domain**
   - Vercel Dashboard → Your Project → Settings → Domains
   - Add domain and configure DNS
   - Update Lambda `FRONTEND_URL` to custom domain

3. **Enable Auto-Deployments**
   - Connect Vercel to your GitHub repo
   - Auto-deploy on push to main branch
