#!/bin/bash

# Simple script to run Bitcoin News Scanner in the foreground
# This will show all output directly in the terminal

# Change to the scanner directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Print banner
echo "======================================"
echo "  Bitcoin News Scanner - Live Output  "
echo "======================================"
echo "Press Ctrl+C to stop the scanner"
echo ""

# Run the scanner in foreground mode
python main.py "$@"

# Note: You'll need to press Ctrl+C to stop the scanner
# The deactivate command won't be reached until you stop the scanner
# deactivate
