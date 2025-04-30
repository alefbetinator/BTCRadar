#!/bin/bash

# Script to test if a single URL qualifies as "under the radar"
# Usage: ./test_single_url.sh URL

# Change to script directory
cd "$(dirname "$0")"

# Check if a URL was provided
if [ $# -ne 1 ]; then
  echo "Usage: $0 <URL>"
  echo "Example: $0 https://example.com/article"
  exit 1
fi

URL="$1"

# Activate virtual environment
source venv/bin/activate

# Run the test_url.py script
python test_url.py "$URL"

# Deactivate virtual environment
deactivate
