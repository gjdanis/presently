#!/bin/bash
# Get JWT token from AWS Cognito
# Usage: ./get-token.sh [dev|prod] <email> <password>

set -e

ENV=${1:-dev}
EMAIL=$2
PASSWORD=$3
REGION="us-east-1"

if [ -z "$EMAIL" ] || [ -z "$PASSWORD" ]; then
    echo "Usage: ./get-token.sh [dev|prod] <email> <password>"
    echo "Example: ./get-token.sh dev user@example.com MyPassword123!"
    exit 1
fi

# Get Cognito User Pool Client ID from SSM
CLIENT_ID=$(aws ssm get-parameter \
    --name "/${ENV}/UserPoolClientId" \
    --region "$REGION" \
    --query 'Parameter.Value' \
    --output text)

echo "Authenticating with Cognito..."
echo "Client ID: $CLIENT_ID"
echo "Email: $EMAIL"
echo ""

# Authenticate and get tokens
RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --client-id "$CLIENT_ID" \
    --auth-parameters USERNAME="$EMAIL",PASSWORD="$PASSWORD" \
    --region "$REGION" \
    --output json 2>&1) || {
    echo "Authentication failed!"
    echo "$RESPONSE"
    exit 1
}

# Extract ID token (JWT)
ID_TOKEN=$(echo "$RESPONSE" | jq -r '.AuthenticationResult.IdToken')
ACCESS_TOKEN=$(echo "$RESPONSE" | jq -r '.AuthenticationResult.AccessToken')
REFRESH_TOKEN=$(echo "$RESPONSE" | jq -r '.AuthenticationResult.RefreshToken')

if [ "$ID_TOKEN" == "null" ] || [ -z "$ID_TOKEN" ]; then
    echo "Failed to get ID token"
    echo "$RESPONSE"
    exit 1
fi

echo "✅ Authentication successful!"
echo ""
echo "============================================"
echo "ID Token (use this for API calls):"
echo "============================================"
echo "$ID_TOKEN"
echo ""
echo "============================================"
echo "Export this token:"
echo "============================================"
echo "export JWT_TOKEN='$ID_TOKEN'"
echo ""
echo "============================================"
echo "Access Token:"
echo "============================================"
echo "$ACCESS_TOKEN"
echo ""
echo "Token expires in 1 hour"
