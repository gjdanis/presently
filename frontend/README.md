# Presently Frontend

Next.js 14 frontend for the Presently wishlist application.

## Prerequisites

### Fix Node.js icu4c Library Issue

If you're encountering the icu4c library error, run:

```bash
# Option 1: Wait for brew reinstall to finish (may take 5-10 minutes)
brew reinstall node

# Option 2: Use nvm (Node Version Manager) instead
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.zshrc  # or ~/.bashrc
nvm install 20
nvm use 20
```

### Verify Node is Working

```bash
node --version  # Should show v20.x.x or v21.x.x
npm --version   # Should show 10.x.x
```

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install all dependencies listed in `package.json`.

### 2. Configure Environment

The `.env.local` file is already created with dev environment settings:

```
NEXT_PUBLIC_API_URL=https://m7oou2xhf0.execute-api.us-east-1.amazonaws.com/dev
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_j7vCYcPVp
NEXT_PUBLIC_COGNITO_CLIENT_ID=6nic4kigvu9mbekahh13nsclpu
NEXT_PUBLIC_COGNITO_REGION=us-east-1
NEXT_PUBLIC_CDN_URL=https://d3h1arh9hpah7a.cloudfront.net
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000)

### 4. Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js 14 App Router
│   ├── layout.tsx         # Root layout with AuthProvider
│   ├── page.tsx           # Landing page
│   ├── globals.css        # Global styles + Tailwind
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # Protected dashboard pages
│   └── invite/            # Public invitation acceptance
├── components/            # Reusable React components
│   └── ui/               # shadcn/ui components
├── lib/                  # Utilities and helpers
│   ├── api.ts           # API client (axios)
│   ├── auth.ts          # Cognito auth functions
│   ├── types.ts         # TypeScript interfaces
│   ├── utils.ts         # Utility functions
│   └── contexts/        # React contexts
│       └── AuthContext.tsx
├── public/              # Static assets
├── .env.local          # Environment variables (git-ignored)
├── tailwind.config.ts  # Tailwind CSS configuration
└── tsconfig.json       # TypeScript configuration
```

## Available Scripts

- `npm run dev` - Start development server on localhost:3000
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check

## Key Features

### Authentication
- **Sign Up**: Register with email, password, and name
- **Email Verification**: Cognito sends verification code
- **Sign In**: JWT-based authentication
- **Auto Profile Creation**: Cognito triggers create profile on signup

### API Integration
- **Automatic Token Attachment**: All requests include JWT token
- **Error Handling**: 401 redirects to login
- **Type Safety**: Full TypeScript types matching backend models

### State Management
- **AuthContext**: Global authentication state
- **React Hooks**: useState, useEffect for local state
- **No Redux**: Simple hooks-based approach for MVP

## Development Workflow

### 1. Create New Feature

```bash
# Work in feature branch
git checkout -b feature/your-feature

# Make changes to files...

# Test locally
npm run dev
```

### 2. Test with Backend

The frontend is configured to use the deployed dev backend API:
- API: `https://m7oou2xhf0.execute-api.us-east-1.amazonaws.com/dev`
- Cognito: `us-east-1_j7vCYcPVp`

You can create test users using the root-level scripts:
```bash
# From project root
./create-test-user.sh dev
./get-token.sh dev
```

### 3. Common Tasks

**Add a New Page:**
1. Create file in `app/` directory (e.g., `app/settings/page.tsx`)
2. Use `'use client'` directive if using hooks/state
3. Add to navigation if needed

**Add a New API Endpoint:**
1. Add method to `lib/api.ts`
2. Add types to `lib/types.ts`
3. Use in components with error handling

**Add UI Components:**
1. Create in `components/` directory
2. Use Tailwind for styling
3. Make reusable with props

## Styling

### Tailwind CSS
- **Dark Mode**: Class-based (`dark` class on html element)
- **Design Tokens**: Defined in `tailwind.config.ts`
- **Global Styles**: In `app/globals.css`

### Color Scheme
- **Primary**: Blue-600 (light) / Blue-400 (dark)
- **Background**: Gray-50 (light) / Gray-900 (dark)
- **Cards**: White (light) / Gray-800 (dark)

### Utility Function
```typescript
import { cn } from '@/lib/utils';

// Merge Tailwind classes
<div className={cn('base-class', condition && 'conditional-class')} />
```

## TypeScript

All components and utilities are fully typed:
- Interfaces in `lib/types.ts` match backend Pydantic models
- Strict mode enabled
- No `any` types (use `unknown` if needed)

## Testing

Currently manual testing. Future:
- Jest + React Testing Library for unit tests
- Playwright for E2E tests

## Troubleshooting

### Node.js Not Found
```bash
# Check if Node is in PATH
which node

# If not, reinstall or use nvm
brew reinstall node
# OR
nvm install 20 && nvm use 20
```

### icu4c Library Error
This is a known issue on macOS. The brew reinstall should fix it.

### API 401 Errors
- Check `.env.local` has correct Cognito settings
- Verify user is signed in
- Check JWT token is being sent in headers

### CORS Errors
- Backend API Gateway should allow `localhost:3000`
- Check API Gateway CORS configuration in CloudFormation

### Build Errors
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

## Next Steps

1. Finish authentication pages (login/register)
2. Build dashboard layout and navigation
3. Create groups management pages
4. Create wishlist management pages
5. Implement purchase claim/unclaim
6. Add photo upload support
7. Test all user flows end-to-end

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API Gateway URL | `https://xxx.execute-api.us-east-1.amazonaws.com/dev` |
| `NEXT_PUBLIC_COGNITO_USER_POOL_ID` | Cognito User Pool ID | `us-east-1_xxxxxxxxx` |
| `NEXT_PUBLIC_COGNITO_CLIENT_ID` | Cognito App Client ID | `xxxxxxxxxxxxxxxx` |
| `NEXT_PUBLIC_COGNITO_REGION` | AWS Region | `us-east-1` |
| `NEXT_PUBLIC_CDN_URL` | CloudFront CDN for photos | `https://xxx.cloudfront.net` |

All variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod
```

Add environment variables in Vercel dashboard.

### Docker
```bash
# Build
docker build -t presently-frontend .

# Run
docker run -p 3000:3000 presently-frontend
```

## Support

- **Backend API**: See `/backend/README.md`
- **Issues**: Check browser console and Network tab
- **Logs**: Next.js logs in terminal where `npm run dev` is running
