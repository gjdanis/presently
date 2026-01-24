#!/bin/bash
# Create a test user in AWS Cognito
# Usage: ./create-test-user.sh [dev|prod] <email> <password> <name>

set -e

ENV=${1:-dev}
EMAIL=$2
PASSWORD=$3
NAME=$4
REGION="us-east-1"

if [ -z "$EMAIL" ] || [ -z "$PASSWORD" ] || [ -z "$NAME" ]; then
    echo "Usage: ./create-test-user.sh [dev|prod] <email> <password> <name>"
    echo "Example: ./create-test-user.sh dev test@example.com TestPass123! 'John Doe'"
    echo ""
    echo "Password requirements:"
    echo "  - At least 8 characters"
    echo "  - Contains uppercase letter"
    echo "  - Contains lowercase letter"
    echo "  - Contains number"
    echo "  - Contains special character"
    exit 1
fi

# Get Cognito User Pool ID from SSM
USER_POOL_ID=$(aws ssm get-parameter \
    --name "/${ENV}/UserPoolId" \
    --region "$REGION" \
    --query 'Parameter.Value' \
    --output text)

CLIENT_ID=$(aws ssm get-parameter \
    --name "/${ENV}/UserPoolClientId" \
    --region "$REGION" \
    --query 'Parameter.Value' \
    --output text)

echo "Creating user in Cognito..."
echo "User Pool: $USER_POOL_ID"
echo "Email: $EMAIL"
echo "Name: $NAME"
echo ""

# Create user
SIGNUP_RESPONSE=$(aws cognito-idp sign-up \
    --client-id "$CLIENT_ID" \
    --username "$EMAIL" \
    --password "$PASSWORD" \
    --user-attributes Name=email,Value="$EMAIL" Name=name,Value="$NAME" \
    --region "$REGION" \
    --output json 2>&1) || {
    echo "Failed to create user!"
    echo "$SIGNUP_RESPONSE"
    exit 1
}

USER_SUB=$(echo "$SIGNUP_RESPONSE" | jq -r '.UserSub')

echo "✅ User created successfully!"
echo "User Sub (ID): $USER_SUB"
echo ""

# Confirm user (skip email verification for testing)
echo "Auto-confirming user (bypassing email verification)..."
aws cognito-idp admin-confirm-sign-up \
    --user-pool-id "$USER_POOL_ID" \
    --username "$EMAIL" \
    --region "$REGION" || {
    echo "Note: Confirmation may have failed if user already confirmed"
}

echo "✅ User confirmed!"
echo ""
echo "✅ Profile automatically created in database via Cognito trigger"
echo ""

# Try to get a token
echo "============================================"
echo "Getting authentication token..."
echo "============================================"
echo ""

sleep 2  # Wait a moment for user to be fully created

./get-token.sh "$ENV" "$EMAIL" "$PASSWORD"
