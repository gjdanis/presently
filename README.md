# Presently

A multi-group wishlist application for families and friends to share gift ideas and secretly claim items for purchase.

## Features

- 🎁 Create and manage wishlists with items, descriptions, links, and photos
- 👥 Organize multiple groups (family, friends, coworkers)
- 🔒 Privacy-first: item owners can't see who purchased their items
- 🎯 Drag-and-drop prioritization for wishlist items
- 🔗 Shareable group invitation links
- 📱 Responsive design for mobile and desktop
- 💰 AWS Free Tier optimized (~$1-2/month)

## Architecture

### Backend
- **Runtime**: Python 3.11
- **API**: AWS Lambda + API Gateway
- **Auth**: AWS Cognito (JWT-based)
- **Database**: Neon Postgres (serverless)
- **Storage**: AWS S3 + CloudFront CDN
- **IaC**: CloudFormation + AWS SAM

### Frontend
- **Framework**: Next.js 14 (React)
- **Hosting**: Vercel
- **Styling**: Tailwind CSS
- **State**: React Hooks + Context

## Quick Start

### Prerequisites

- Python 3.11+
- AWS CLI configured
- AWS SAM CLI installed
- PostgreSQL client (psql)
- Neon database account

### 1. Clone and Setup

```bash
git clone <repo-url>
cd presently

# Create virtual environment and install dependencies
make install-dev
```

### 2. Development

```bash
# Format code
make format

# Run linter
make lint

# Run tests
make test

# Run tests with coverage
make test-cov
```

### 3. Deploy

```bash
# Set your Neon database URL
export DATABASE_URL='postgresql://user:pass@ep-xxx.neon.tech/presently?sslmode=require'

# Deploy everything
make deploy ENV=prod

# Run database migrations
make db-migrate
```

See [backend/README.md](backend/README.md) for detailed deployment instructions.

## Project Structure

```
presently/
├── backend/
│   ├── lambda/              # Lambda function code
│   │   ├── common/          # Shared utilities
│   │   │   ├── auth.py      # Cognito JWT verification
│   │   │   ├── db.py        # Database connections
│   │   │   ├── models.py    # Pydantic models
│   │   │   └── responses.py # HTTP helpers
│   │   ├── routers/         # API endpoints (FastAPI)
│   │   │   ├── profile.py   # User profiles
│   │   │   ├── groups.py    # Group management
│   │   │   ├── wishlist.py  # Wishlist CRUD
│   │   │   ├── purchases.py # Purchase tracking
│   │   │   ├── invitations.py# Group invites
│   │   │   └── photos.py    # Photo uploads
│   │   ├── services/        # Business logic
│   │   └── repositories/    # Data access
│   ├── migrations/          # Database schema
│   ├── tests/               # Unit tests
│   └── venv/               # Virtual environment (created by make)
├── infrastructure/
│   ├── cloudformation/      # Infrastructure as Code
│   └── scripts/             # Deployment scripts
└── frontend/               # Next.js app

```

## Virtual Environment

The project uses a local Python virtual environment in `backend/venv/`.

### Automatic (via Makefile)

All `make` commands automatically use the virtual environment:

```bash
make install-dev  # Creates venv + installs deps
make test         # Runs tests in venv
make format       # Formats code in venv
```

### Manual Activation

```bash
# Option 1: Use helper script
source backend/activate.sh

# Option 2: Direct activation
source backend/venv/bin/activate

# Deactivate when done
deactivate
```

## Available Commands

```bash
make help          # Show all available commands
make venv          # Create virtual environment only
make install-dev   # Install all dependencies (dev + prod)
make install       # Install production dependencies only
make test          # Run tests
make test-cov      # Run tests with coverage report
make lint          # Run ruff linter
make format        # Format code with ruff
make check         # Type check with mypy
make clean         # Remove build artifacts
make clean-all     # Remove build artifacts + venv
make deploy        # Deploy everything to AWS
make db-migrate    # Run database migrations
```

## API Endpoints

### Authentication
All endpoints require `Authorization: Bearer <JWT>` header (except where noted).

### Profiles
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile

### Groups
- `GET /groups` - List user's groups
- `POST /groups` - Create new group
- `GET /groups/{id}` - Get group details + wishlists
- `PUT /groups/{id}` - Update group (admin only)
- `DELETE /groups/{id}` - Delete group (admin only)

### Wishlist
- `GET /wishlist` - Get user's items
- `POST /wishlist` - Create item
- `GET /wishlist/{id}` - Get item
- `PUT /wishlist/{id}` - Update item
- `DELETE /wishlist/{id}` - Delete item
- `PUT /wishlist/reorder` - Reorder items

### Purchases
- `POST /purchases` - Claim item
- `DELETE /purchases/{itemId}/{groupId}` - Unclaim item

### Invitations
- `GET /invitations/{token}` - Get invite (public)
- `POST /invitations/{token}/accept` - Accept invite
- `POST /groups/{id}/members` - Send invite
- `DELETE /groups/{id}/members/{userId}` - Remove member

### Photos
- `POST /photos/upload` - Get S3 upload URL

## Development Workflow

### 1. Create a Feature

```bash
# Create branch
git checkout -b feature/your-feature

# Make changes
# Edit files...

# Format and lint
make format lint

# Run tests
make test-cov

# Commit
git add .
git commit -m "Add your feature"
```

### 2. Pre-commit Checks

```bash
# Run all checks before committing
make pre-commit
```

This runs: format → lint → test

### 3. Deploy Changes

```bash
# Deploy to dev environment
export DATABASE_URL='...'
make deploy ENV=dev

# Test in dev, then deploy to prod
make deploy ENV=prod
```

## Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-cov
open backend/htmlcov/index.html

# Run specific test file
source backend/venv/bin/activate
pytest backend/tests/test_profile.py -v

# Run specific test function
pytest backend/tests/test_profile.py::test_get_profile_success -v
```

## Code Style

- **Formatter**: Ruff (100 char lines)
- **Linter**: Ruff
- **Type Checker**: mypy
- **Models**: Pydantic (no dictionaries for structured data)
- **Imports**: Sorted automatically by ruff

## Cost Estimate

### Free Tier (< 50 users, < 1M requests/month)
- Cognito: $0
- API Gateway: $0
- Lambda: $0
- Neon Postgres: $0
- S3: ~$0.25/month
- CloudFront: ~$0.85/month
- **Total: ~$1-2/month**

### Beyond Free Tier (100 users, 3M requests/month)
- Cognito: $0 (still free)
- API Gateway: +$7/month
- Lambda: +$0.40/month
- Neon: $0 (still < 0.5GB)
- S3 + CDN: ~$2/month
- **Total: ~$10-15/month**

## Security

- ✅ JWT authentication via AWS Cognito
- ✅ SQL injection prevention (parameterized queries)
- ✅ Input validation with Pydantic
- ✅ Secrets in environment variables
- ✅ HTTPS only
- ✅ S3 presigned URLs for uploads
- ✅ CORS configured

## Monitoring

```bash
# View Lambda logs
aws logs tail /aws/lambda/presently-lambda-prod-GroupsFunction --follow

# View API Gateway logs
aws logs tail /aws/apigateway/presently-api-prod --follow

# Check stack status
aws cloudformation describe-stacks --stack-name presently-infra-prod
```

## Troubleshooting

### Virtual Environment Issues

```bash
# Recreate virtual environment
make clean-all
make install-dev
```

### Database Connection Issues

```bash
# Test connection
psql "$DATABASE_URL" -c "SELECT 1"

# View tables
make db-shell
\dt
```

### Deployment Issues

```bash
# View CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name presently-infra-prod \
  --max-items 10

# Check SSM parameters
aws ssm get-parameters-by-path --path /prod
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run `make pre-commit` to ensure quality
5. Submit a pull request

## License

MIT

## Support

- Documentation: See [backend/README.md](backend/README.md)
- Issues: Open a GitHub issue
- Questions: Check CloudWatch logs and CloudFormation events
