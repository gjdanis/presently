#!/bin/bash
set -e

# Deploy Lambda functions using AWS SAM
# Usage: ./deploy-lambda.sh <environment>

ENV=${1:-dev}

echo "🚀 Deploying Lambda functions for environment: $ENV"

# Validate environment
if [[ ! "$ENV" =~ ^(dev|prod)$ ]]; then
    echo "❌ Error: Environment must be 'dev' or 'prod'"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL environment variable is required"
    echo "   Set it with your Neon Postgres connection string:"
    echo "   export DATABASE_URL='postgresql://user:pass@host/db'"
    exit 1
fi

# Check if SENDER_EMAIL is set
if [ -z "$SENDER_EMAIL" ]; then
    echo "❌ Error: SENDER_EMAIL environment variable is required"
    echo "   Set it with your verified SES email address:"
    echo "   export SENDER_EMAIL='your-email@example.com'"
    exit 1
fi

STACK_NAME="presently-lambda-$ENV"
REGION="us-east-1"

echo "📦 Building SAM application..."
echo "📍 Region: $REGION"
cd ../backend/lambda
sam build

echo "📦 Deploying stack: $STACK_NAME"
sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --parameter-overrides \
        Environment="$ENV" \
        NeonDatabaseURL="$DATABASE_URL" \
        SenderEmail="$SENDER_EMAIL" \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --no-fail-on-empty-changeset

echo "✅ Lambda deployment complete!"

# Output API endpoint
echo ""
echo "📋 API Gateway URL:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text

echo ""
echo "💡 Use this URL for NEXT_PUBLIC_API_URL in your frontend"
