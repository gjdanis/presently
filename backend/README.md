# Presently Backend

Python-based AWS Lambda backend for the Presently wishlist application.

## Architecture

- **Language**: Python 3.11
- **Framework**: FastAPI + AWS Lambda (via Mangum)
- **Database**: Neon Postgres (serverless)
- **Auth**: AWS Cognito
- **Storage**: AWS S3 + CloudFront CDN
- **IaC**: CloudFormation + AWS SAM

## Project Structure

```
backend/
├── lambda/
│   ├── common/              # Shared utilities
│   │   ├── auth.py          # Cognito JWT verification
│   │   ├── db.py            # Database connections
│   │   ├── models.py        # Pydantic models
│   │   └── responses.py     # HTTP response helpers
│   ├── routers/             # API endpoints (FastAPI routers)
│   │   ├── profile.py       # Profile management
│   │   ├── groups.py        # Group CRUD
│   │   ├── wishlist.py      # Wishlist CRUD
│   │   ├── purchases.py     # Purchase tracking
│   │   ├── invitations.py   # Group invitations
│   │   └── photos.py        # Photo uploads
│   ├── services/            # Business logic layer
│   ├── repositories/        # Data access layer
│   ├── main.py              # FastAPI app entry point
│   └── template.yaml        # SAM template
├── migrations/
│   └── schema.sql           # Database schema
├── tests/                   # Unit tests
├── requirements.txt         # All dependencies
└── requirements-layer.txt   # Production dependencies only
```

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL client (for database migrations)
- AWS CLI configured
- AWS SAM CLI installed

### Install Dependencies

```bash
# Install development dependencies
make install-dev

# Or just production dependencies
make install
```

### Environment Variables

Create a `.env` file (not committed to git):

```bash
DATABASE_URL=postgresql://user:password@host/database
COGNITO_USER_POOL_ID=us-east-1_XXXXXXX
COGNITO_CLIENT_ID=xxxxxxxxxxxx
AWS_REGION=us-east-1
PHOTOS_BUCKET=presently-photos-dev
PHOTOS_CDN=d123456.cloudfront.net
```

## Development Workflow

### Code Quality

```bash
# Format code with ruff
make format

# Run linter
make lint

# Type checking
make check

# Run all checks
make format lint check
```

### Testing

```bash
# Run tests with coverage
make test

# View coverage report
open htmlcov/index.html
```

### Database

```bash
# Run migrations
make db-migrate DATABASE_URL='postgresql://...'

# Open database shell
make db-shell DATABASE_URL='postgresql://...'
```

## Deployment

### 1. Deploy Infrastructure (Cognito + S3)

```bash
make deploy-infra ENV=prod
```

This creates:
- Cognito User Pool
- S3 bucket for photos
- CloudFront CDN
- Lambda execution role

### 2. Set Up Database

```bash
# Create Neon database at https://neon.tech (free tier)
# Get connection string and set environment variable

export DATABASE_URL='postgresql://user:pass@ep-xxx.neon.tech/presently?sslmode=require'

# Run migrations
make db-migrate
```

### 3. Deploy Lambda Functions

```bash
make deploy-lambda ENV=prod
```

This deploys all Lambda functions and API Gateway.

### Full Deployment

```bash
# Deploy everything at once
export DATABASE_URL='postgresql://...'
make deploy ENV=prod
```

## API Endpoints

All endpoints require authentication via `Authorization: Bearer <JWT>` header (except where noted).

### Profile
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile

### Groups
- `GET /groups` - List user's groups
- `POST /groups` - Create group
- `GET /groups/{groupId}` - Get group details with wishlists
- `PUT /groups/{groupId}` - Update group (admin only)
- `DELETE /groups/{groupId}` - Delete group (admin only)

### Wishlist
- `GET /wishlist` - Get user's wishlist items
- `POST /wishlist` - Create wishlist item
- `GET /wishlist/{itemId}` - Get item details
- `PUT /wishlist/{itemId}` - Update item
- `DELETE /wishlist/{itemId}` - Delete item
- `PUT /wishlist/reorder` - Reorder items

### Purchases
- `POST /purchases` - Claim item as purchased
- `DELETE /purchases/{itemId}/{groupId}` - Unclaim item

### Invitations
- `GET /invitations/{token}` - Get invitation details (public)
- `POST /invitations/{token}/accept` - Accept invitation
- `POST /groups/{groupId}/members` - Send invitation
- `DELETE /groups/{groupId}/members/{memberId}` - Remove member

### Photos
- `POST /photos/upload` - Get presigned S3 upload URL

## Code Style

- **Formatting**: Ruff (100 char line length)
- **Type hints**: Required for all functions
- **Docstrings**: Google style for public functions
- **Models**: Pydantic models for all data structures
- **Imports**: Sorted with isort (via ruff)

## Testing Guidelines

- Write tests for all handlers
- Use mocks for database and external services
- Aim for >80% code coverage
- Test both success and error cases

## Monitoring

Logs are automatically sent to CloudWatch Logs:

```bash
# View logs for a specific function
aws logs tail /aws/lambda/presently-lambda-prod-ProfileFunction --follow
```

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
psql "$DATABASE_URL" -c "SELECT 1"

# Check Neon dashboard for connection limits
```

### Lambda Cold Starts

- Functions use connection pooling to reuse DB connections
- First invocation may be slower (~1-2s)
- Subsequent invocations are fast (~100-200ms)

### Authentication Errors

```bash
# Verify Cognito configuration
aws cognito-idp describe-user-pool --user-pool-id <pool-id>

# Check token expiration (default: 1 hour)
```

## Cost Optimization

- **Lambda**: Use ARM64 architecture (cheaper)
- **S3**: Enable lifecycle policies to delete old files
- **CloudFront**: Use PriceClass_100 (cheapest regions)
- **Neon**: Stay under 0.5GB for free tier

## Security Best Practices

- ✅ All endpoints require authentication (except public invite page)
- ✅ SQL injection prevention via parameterized queries
- ✅ Input validation with Pydantic
- ✅ Secrets stored in environment variables
- ✅ S3 presigned URLs for secure uploads
- ✅ HTTPS only (enforced by API Gateway)

## Contributing

1. Create a feature branch
2. Make changes
3. Run `make pre-commit` to ensure quality
4. Submit pull request

## License

MIT
