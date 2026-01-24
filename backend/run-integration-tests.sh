#!/bin/bash

set -e

echo "Running integration tests..."
cd /Users/joe/Documents/presently/backend
pytest tests/integration/test_groups_integration.py tests/integration/test_wishlist_integration.py -v
