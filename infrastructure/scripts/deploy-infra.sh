#!/bin/bash
set -e

# Deploy Cognito + S3 infrastructure
# Usage: ./deploy-infra.sh <environment>

ENV=${1:-dev}

echo "🚀 Deploying infrastructure for environment: $ENV"

# Validate environment
if [[ ! "$ENV" =~ ^(dev|prod)$ ]]; then
    echo "❌ Error: Environment must be 'dev' or 'prod'"
    exit 1
fi

STACK_NAME="presently-infra-$ENV"
TEMPLATE_FILE="cloudformation/cognito-s3.yaml"
REGION="us-east-1"

echo "📦 Deploying stack: $STACK_NAME"
echo "📍 Region: $REGION"

aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides Environment="$ENV" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --no-fail-on-empty-changeset

echo "✅ Infrastructure deployment complete!"

# Store outputs in SSM Parameter Store for Lambda deployment
echo ""
echo "📦 Storing stack outputs in SSM Parameter Store..."

get_output() {
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" \
        --output text
}

# Store each output as SSM parameter
aws ssm put-parameter \
    --name "/$ENV/UserPoolId" \
    --value "$(get_output UserPoolId)" \
    --type String \
    --region "$REGION" \
    --overwrite >/dev/null 2>&1 || true

aws ssm put-parameter \
    --name "/$ENV/UserPoolClientId" \
    --value "$(get_output UserPoolClientId)" \
    --type String \
    --region "$REGION" \
    --overwrite >/dev/null 2>&1 || true

aws ssm put-parameter \
    --name "/$ENV/UserPoolArn" \
    --value "$(get_output UserPoolArn)" \
    --type String \
    --region "$REGION" \
    --overwrite >/dev/null 2>&1 || true

aws ssm put-parameter \
    --name "/$ENV/PhotosBucket" \
    --value "$(get_output PhotosBucketName)" \
    --type String \
    --region "$REGION" \
    --overwrite >/dev/null 2>&1 || true

aws ssm put-parameter \
    --name "/$ENV/PhotosCDN" \
    --value "$(get_output PhotosCDNDomain)" \
    --type String \
    --region "$REGION" \
    --overwrite >/dev/null 2>&1 || true

aws ssm put-parameter \
    --name "/$ENV/LambdaRole" \
    --value "$(get_output LambdaRoleArn)" \
    --type String \
    --region "$REGION" \
    --overwrite >/dev/null 2>&1 || true

echo "✅ SSM parameters updated"

# Output important values
echo ""
echo "📋 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo ""
echo "💡 Next steps:"
echo "   1. Set DATABASE_URL environment variable with your Neon connection string"
echo "   2. Run: make db-migrate DATABASE_URL='<your-neon-url>'"
echo "   3. Deploy Lambda functions: make deploy-lambda ENV=$ENV"
