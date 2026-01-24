#!/bin/bash
# Configure Cognito Lambda triggers
# Usage: ./configure-cognito-triggers.sh <environment>

set -e

ENV=${1:-dev}
REGION="us-east-1"

echo "🔧 Configuring Cognito Lambda triggers for environment: $ENV"

# Validate environment
if [[ ! "$ENV" =~ ^(dev|prod)$ ]]; then
    echo "❌ Error: Environment must be 'dev' or 'prod'"
    exit 1
fi

# Get Cognito User Pool ID
USER_POOL_ID=$(aws ssm get-parameter \
    --name "/${ENV}/UserPoolId" \
    --region "$REGION" \
    --query 'Parameter.Value' \
    --output text)

# Get Lambda function ARNs from CloudFormation stack
LAMBDA_STACK_NAME="presently-lambda-$ENV"

POST_CONFIRMATION_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$LAMBDA_STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PostConfirmationFunctionArn`].OutputValue' \
    --output text)

PRE_SIGNUP_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$LAMBDA_STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PreSignupFunctionArn`].OutputValue' \
    --output text)

echo "User Pool ID: $USER_POOL_ID"
echo "Post-Confirmation ARN: $POST_CONFIRMATION_ARN"
echo "Pre-Signup ARN: $PRE_SIGNUP_ARN"
echo ""

# Add Lambda permissions for Cognito to invoke the functions
echo "📝 Adding Lambda invoke permissions..."

aws lambda add-permission \
    --function-name "$POST_CONFIRMATION_ARN" \
    --statement-id "AllowCognitoInvoke-$ENV" \
    --action lambda:InvokeFunction \
    --principal cognito-idp.amazonaws.com \
    --source-arn "arn:aws:cognito-idp:${REGION}:$(aws sts get-caller-identity --query Account --output text):userpool/${USER_POOL_ID}" \
    --region "$REGION" \
    2>/dev/null || echo "Permission already exists for PostConfirmation"

aws lambda add-permission \
    --function-name "$PRE_SIGNUP_ARN" \
    --statement-id "AllowCognitoInvoke-$ENV" \
    --action lambda:InvokeFunction \
    --principal cognito-idp.amazonaws.com \
    --source-arn "arn:aws:cognito-idp:${REGION}:$(aws sts get-caller-identity --query Account --output text):userpool/${USER_POOL_ID}" \
    --region "$REGION" \
    2>/dev/null || echo "Permission already exists for PreSignup"

# Update infrastructure stack with Lambda trigger ARNs
echo "🔧 Updating infrastructure stack with Lambda triggers..."

INFRA_STACK_NAME="presently-infra-$ENV"

aws cloudformation update-stack \
    --stack-name "$INFRA_STACK_NAME" \
    --region "$REGION" \
    --use-previous-template \
    --parameters \
        ParameterKey=Environment,UsePreviousValue=true \
        ParameterKey=PostConfirmationLambdaArn,ParameterValue="$POST_CONFIRMATION_ARN" \
        ParameterKey=PreSignUpLambdaArn,ParameterValue="$PRE_SIGNUP_ARN" \
    --capabilities CAPABILITY_NAMED_IAM

echo "⏳ Waiting for stack update to complete..."
aws cloudformation wait stack-update-complete \
    --stack-name "$INFRA_STACK_NAME" \
    --region "$REGION"

echo ""
echo "✅ Cognito Lambda triggers configured successfully!"
echo ""
echo "📋 Configured triggers:"
echo "   - PostConfirmation: Automatically creates profile in database"
echo "   - PreSignUp: Auto-confirms users in dev environment"
echo ""
echo "💡 Next steps:"
echo "   Test by creating a new user with: ./create-test-user.sh $ENV user@example.com Password123! 'Test User'"
