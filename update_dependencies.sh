#!/bin/bash

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies from requirements.txt
pip install -r requirements.txt

echo "Dependencies updated successfully!"
