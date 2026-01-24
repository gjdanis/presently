#!/bin/bash
# API Testing Script for Presently
# Usage: ./test-api.sh [dev|prod]

set -e

ENV=${1:-dev}
REGION="us-east-1"

# Get API URL from CloudFormation stack
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "presently-lambda-${ENV}" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null) || {
    echo "❌ Error: Could not find API URL. Has the Lambda stack been deployed?"
    echo "Run: make deploy-lambda ENV=${ENV}"
    exit 1
}

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# You'll need to set this after creating a user in Cognito
# Get it by signing in through Cognito
JWT_TOKEN="${JWT_TOKEN:-}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Presently API (${ENV})${NC}"
echo -e "${BLUE}API URL: ${API_URL}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Helper function to make authenticated requests
auth_request() {
    local method=$1
    local path=$2
    local data=$3

    if [ -z "$JWT_TOKEN" ]; then
        echo -e "${RED}ERROR: JWT_TOKEN not set${NC}"
        echo "Please set JWT_TOKEN environment variable with a valid Cognito token"
        echo "Example: export JWT_TOKEN='eyJraWQiOiJxxx...'"
        exit 1
    fi

    if [ -n "$data" ]; then
        curl -X "$method" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${API_URL}${path}" \
            -w "\nHTTP Status: %{http_code}\n" \
            -s
    else
        curl -X "$method" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            "${API_URL}${path}" \
            -w "\nHTTP Status: %{http_code}\n" \
            -s
    fi
}

# Test 1: Get Profile (requires auth)
echo -e "${GREEN}Test 1: GET /profile${NC}"
auth_request GET /profile
echo -e "\n"

# Test 2: Update Profile (requires auth)
echo -e "${GREEN}Test 2: PUT /profile${NC}"
auth_request PUT /profile '{
  "name": "Test User Updated"
}'
echo -e "\n"

# Test 3: Create Group (requires auth)
echo -e "${GREEN}Test 3: POST /groups${NC}"
GROUP_RESPONSE=$(auth_request POST /groups '{
  "name": "Test Family",
  "description": "Testing group creation"
}')
echo "$GROUP_RESPONSE"
GROUP_ID=$(echo "$GROUP_RESPONSE" | head -1 | jq -r '.id // empty')
echo -e "\n"

# Test 4: Get Groups (requires auth)
echo -e "${GREEN}Test 4: GET /groups${NC}"
auth_request GET /groups
echo -e "\n"

# Test 5: Get Group Details (requires auth)
if [ -n "$GROUP_ID" ]; then
    echo -e "${GREEN}Test 5: GET /groups/${GROUP_ID}${NC}"
    auth_request GET "/groups/${GROUP_ID}"
    echo -e "\n"
fi

# Test 6: Create Wishlist Item (requires auth)
echo -e "${GREEN}Test 6: POST /wishlist${NC}"
ITEM_RESPONSE=$(auth_request POST /wishlist "{
  \"name\": \"Test Item\",
  \"description\": \"A test wishlist item\",
  \"url\": \"https://example.com/product\",
  \"price\": 99.99,
  \"group_ids\": [${GROUP_ID:+\"$GROUP_ID\"}]
}")
echo "$ITEM_RESPONSE"
ITEM_ID=$(echo "$ITEM_RESPONSE" | head -1 | jq -r '.id // empty')
echo -e "\n"

# Test 7: Get Wishlist (requires auth)
echo -e "${GREEN}Test 7: GET /wishlist${NC}"
auth_request GET /wishlist
echo -e "\n"

# Test 8: Update Wishlist Item (requires auth)
if [ -n "$ITEM_ID" ]; then
    echo -e "${GREEN}Test 8: PUT /wishlist/${ITEM_ID}${NC}"
    auth_request PUT "/wishlist/${ITEM_ID}" '{
      "name": "Updated Test Item",
      "price": 89.99
    }'
    echo -e "\n"
fi

# Test 9: Get Public Invitation (no auth required)
echo -e "${GREEN}Test 9: GET /invitations/{token} (testing with fake token)${NC}"
curl -X GET \
    "${API_URL}/invitations/test-token-12345" \
    -w "\nHTTP Status: %{http_code}\n" \
    -s
echo -e "\n"

# Test 10: Delete Wishlist Item (requires auth)
if [ -n "$ITEM_ID" ]; then
    echo -e "${GREEN}Test 10: DELETE /wishlist/${ITEM_ID}${NC}"
    auth_request DELETE "/wishlist/${ITEM_ID}"
    echo -e "\n"
fi

# Test 11: Delete Group (requires auth)
if [ -n "$GROUP_ID" ]; then
    echo -e "${GREEN}Test 11: DELETE /groups/${GROUP_ID}${NC}"
    auth_request DELETE "/groups/${GROUP_ID}"
    echo -e "\n"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Complete${NC}"
echo -e "${BLUE}========================================${NC}"
