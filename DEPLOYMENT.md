# Presently Deployment Guide

Complete guide to deploying Presently backend infrastructure and API.

## Prerequisites

✅ **AWS Account** with admin access
✅ **AWS CLI** installed and configured (`aws configure`)
✅ **AWS SAM CLI** installed ([installation guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
✅ **PostgreSQL client** (`psql`) installed
✅ **Neon account** created at https://neon.tech (free tier)
✅ **Python 3.11+** installed

## Quick Start

### One-Command Deployment

```bash
# Set your Neon database connection string
export DATABASE_URL='postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/presently?sslmode=require'

# Deploy everything (infrastructure + Lambda + migrations)
make deploy ENV=prod && make db-migrate
```

That's it! Your API will be deployed and ready to use.

---

## Detailed Deployment Steps

### Step 1: Set Up Neon Database

1. Go to https://neon.tech and create a free account
2. Create a new project called "presently"
3. Copy the connection string (looks like `postgresql://user:pass@ep-xxx.neon.tech/presently`)
4. Export it as an environment variable:

```bash
export DATABASE_URL='postgresql://user:pass@ep-xxx.neon.tech/presently?sslmode=require'
```

### Step 2: Deploy Infrastructure

This deploys Cognito, S3, CloudFront, and IAM roles:

```bash
make deploy-infra ENV=prod
```

**What this creates:**
- ✅ Cognito User Pool for authentication
- ✅ S3 bucket for photo storage
- ✅ CloudFront CDN for fast photo delivery
- ✅ Lambda execution role with S3 permissions
- ✅ SSM parameters for cross-stack references

**Expected output:**
```
🚀 Deploying infrastructure for environment: prod
📦 Deploying stack: presently-infra-prod
✅ Infrastructure deployment complete!
📦 Storing stack outputs in SSM Parameter Store...
✅ SSM parameters updated

📋 Stack Outputs:
------------------------------------------------
|              DescribeStacks                  |
+-------------------+--------------------------+
|  UserPoolId       |  us-east-1_ABC123       |
|  UserPoolClientId |  xyz789abc123           |
|  PhotosBucket     |  presently-photos-prod  |
|  PhotosCDN        |  d123xyz.cloudfront.net |
+-------------------+--------------------------+
```

### Step 3: Run Database Migrations

Apply the database schema to your Neon database:

```bash
make db-migrate
```

**What this does:**
- Creates all tables (profiles, groups, wishlist_items, etc.)
- Sets up indexes for performance
- Adds triggers for updated_at timestamps

**Expected output:**
```
Running database migrations...
CREATE EXTENSION
CREATE TABLE
CREATE INDEX
...
✅ Database schema created successfully
```

### Step 4: Deploy Lambda Functions

This deploys all API endpoints:

```bash
make deploy-lambda ENV=prod
```

**What this creates:**
- ✅ API Gateway REST API
- ✅ Lambda functions for all handlers
- ✅ Cognito authorizer for protected endpoints
- ✅ CORS configuration

**Expected output:**
```
🚀 Deploying Lambda functions for environment: prod
📦 Building SAM application...
Build Succeeded
📦 Deploying stack: presently-lambda-prod
✅ Lambda deployment complete!

📋 API Gateway URL:
https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
```

### Step 5: Test Your API

```bash
# Get the API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name presently-lambda-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

echo "Your API URL: $API_URL"

# Test the health endpoint (if you add one)
curl $API_URL/health
```

---

## Full Deployment (All Steps Combined)

```bash
# 1. Set environment variables
export DATABASE_URL='postgresql://user:pass@ep-xxx.neon.tech/presently?sslmode=require'

# 2. Deploy everything
make deploy ENV=prod

# 3. Run database migrations
make db-migrate

# 4. Done! Get your API URL
aws cloudformation describe-stacks \
  --stack-name presently-lambda-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text
```

---

## Environment Variables Summary

The `make deploy` command requires:

| Variable | Description | Example |
|----------|-------------|---------|
| `ENV` | Environment name (`dev` or `prod`) | `prod` |
| `DATABASE_URL` | Neon Postgres connection string | `postgresql://user:pass@host/db` |

The Lambda functions will automatically receive these from SSM:
- `COGNITO_USER_POOL_ID`
- `COGNITO_CLIENT_ID`
- `PHOTOS_BUCKET`
- `PHOTOS_CDN`
- `AWS_REGION`

---

## Updating Deployments

### Update Infrastructure Only

```bash
# After changing cloudformation/cognito-s3.yaml
make deploy-infra ENV=prod
```

### Update Lambda Functions Only

```bash
# After changing handler code
export DATABASE_URL='postgresql://...'
make deploy-lambda ENV=prod
```

### Update Database Schema

```bash
# After modifying migrations/schema.sql
make db-migrate
```

**⚠️ Warning:** Running migrations again will attempt to create tables that already exist. For production, use proper migration tools like Alembic or Flyway.

---

## Development vs Production

### Development Environment

```bash
export DATABASE_URL='postgresql://dev-user:pass@dev-host/presently_dev'
make deploy ENV=dev
make db-migrate
```

### Production Environment

```bash
export DATABASE_URL='postgresql://prod-user:pass@prod-host/presently'
make deploy ENV=prod
make db-migrate
```

**Stack names:**
- Dev: `presently-infra-dev`, `presently-lambda-dev`
- Prod: `presently-infra-prod`, `presently-lambda-prod`

---

## Verifying Deployment

### Check Infrastructure Stack

```bash
aws cloudformation describe-stacks \
  --stack-name presently-infra-prod \
  --query 'Stacks[0].StackStatus'
```

Expected: `CREATE_COMPLETE` or `UPDATE_COMPLETE`

### Check Lambda Stack

```bash
aws cloudformation describe-stacks \
  --stack-name presently-lambda-prod \
  --query 'Stacks[0].StackStatus'
```

Expected: `CREATE_COMPLETE` or `UPDATE_COMPLETE`

### Check Database Tables

```bash
psql "$DATABASE_URL" -c "\dt"
```

Expected output:
```
                List of relations
 Schema |         Name          | Type  |  Owner
--------+-----------------------+-------+---------
 public | profiles              | table | user
 public | groups                | table | user
 public | group_memberships     | table | user
 public | wishlist_items        | table | user
 public | item_group_assignments| table | user
 public | purchases             | table | user
 public | group_invitations     | table | user
```

### Test API Endpoints

```bash
# Get API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name presently-lambda-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text)

# Test public invitation endpoint (no auth required)
curl $API_URL/invitations/test-token
# Expected: 404 (token doesn't exist, but endpoint works)
```

---

## Troubleshooting

### Issue: "DATABASE_URL environment variable is required"

**Solution:**
```bash
export DATABASE_URL='postgresql://user:pass@host/db'
```

### Issue: "Stack already exists"

**Solution:** CloudFormation will update the existing stack automatically. This is normal.

### Issue: "Invalid permissions on Lambda execution role"

**Solution:** The infrastructure stack creates the role. Make sure you ran `make deploy-infra` first.

### Issue: "SSM parameter not found"

**Solution:** The `deploy-infra.sh` script populates SSM parameters. Run:
```bash
make deploy-infra ENV=prod
```

### Issue: "Database connection refused"

**Solution:**
1. Check Neon dashboard for connection string
2. Verify your IP is allowed (Neon allows all by default)
3. Test connection manually:
```bash
psql "$DATABASE_URL" -c "SELECT 1"
```

### View Lambda Logs

```bash
# Tail logs for a specific function
aws logs tail /aws/lambda/presently-lambda-prod-GroupsFunction --follow

# Or use SAM
sam logs --stack-name presently-lambda-prod --name GroupsFunction --tail
```

---

## Cost Estimate

### Free Tier (Expected: $0-2/month)

- ✅ **Cognito**: Free (< 50k MAU)
- ✅ **API Gateway**: Free (< 1M requests/month)
- ✅ **Lambda**: Free (< 1M requests/month)
- ✅ **Neon Postgres**: Free (< 0.5GB storage)
- 💰 **S3**: ~$0.23/month (10GB photos)
- 💰 **CloudFront**: ~$0.85/month (10GB transfer)

**Total: ~$1-2/month** for personal/family use

### Beyond Free Tier

At 100 users, 3M requests/month:
- API Gateway: +$7/month
- Lambda: +$0.40/month
- S3: +$1/month
- **Total: ~$10-15/month**

---

## Cleanup (Delete Everything)

### Delete Lambda Functions

```bash
aws cloudformation delete-stack --stack-name presently-lambda-prod
aws cloudformation wait stack-delete-complete --stack-name presently-lambda-prod
```

### Delete Infrastructure

```bash
# Empty S3 bucket first (required)
aws s3 rm s3://presently-photos-prod --recursive

# Delete stack
aws cloudformation delete-stack --stack-name presently-infra-prod
aws cloudformation wait stack-delete-complete --stack-name presently-infra-prod
```

### Delete SSM Parameters

```bash
aws ssm delete-parameter --name /prod/UserPoolId
aws ssm delete-parameter --name /prod/UserPoolClientId
aws ssm delete-parameter --name /prod/UserPoolArn
aws ssm delete-parameter --name /prod/PhotosBucket
aws ssm delete-parameter --name /prod/PhotosCDN
aws ssm delete-parameter --name /prod/LambdaRole
```

### Delete Neon Database

Go to https://console.neon.tech and delete the project manually.

---

## Next Steps

After deployment:

1. **Save your API URL** for frontend configuration
2. **Save Cognito User Pool ID and Client ID** for frontend auth
3. **Test user registration** via Cognito
4. **Create a test user** and verify profile creation
5. **Deploy frontend** to Vercel with API URL

---

## Support

For issues:
- Check CloudFormation stack events for errors
- Review Lambda logs in CloudWatch
- Verify SSM parameters are populated
- Test database connection manually

Common commands:
```bash
# View infrastructure stack events
aws cloudformation describe-stack-events \
  --stack-name presently-infra-prod \
  --max-items 10

# View Lambda stack events
aws cloudformation describe-stack-events \
  --stack-name presently-lambda-prod \
  --max-items 10

# List all SSM parameters
aws ssm get-parameters-by-path --path /prod
```
