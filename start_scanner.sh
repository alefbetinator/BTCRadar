#!/bin/bash

# Bitcoin News Scanner Startup Script
# This script starts the Bitcoin News Scanner and optionally the web UI

# Change to the script's directory
cd "$(dirname "$0")"

# Configuration
SCANNER_LOG="logs/scanner.log"
WEB_UI_LOG="logs/web_ui.log"
SHOW_RECENT=false
START_WEB_UI=false
FORCE_RESCAN=false

# Create logs directory if it doesn't exist
mkdir -p logs

# Print banner
echo "================================="
echo "  Bitcoin News Scanner Launcher  "
echo "================================="

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --web-ui)
      START_WEB_UI=true
      shift
      ;;
    --show-recent)
      SHOW_RECENT=true
      shift
      ;;
    --force-rescan)
      FORCE_RESCAN=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --web-ui        Start the web UI"
      echo "  --show-recent   Show recent opportunities when starting"
      echo "  --force-rescan  Force rescan of articles"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Function to check if Python virtual environment exists
check_venv() {
  if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
  else
    source venv/bin/activate
  fi
}

# Function to check if env file exists
check_env_file() {
  if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Creating from template..."
    cp .env.template .env
    echo "Please edit .env file with your settings before using the scanner."
    exit 1
  fi
}

# Function to start the scanner
start_scanner() {
  echo "Starting Bitcoin News Scanner..."
  
  # Build command based on options
  CMD="python main.py"
  if [ "$SHOW_RECENT" = true ]; then
    CMD="$CMD --show-recent"
  fi
  if [ "$FORCE_RESCAN" = true ]; then
    CMD="$CMD --force-rescan"
  fi
  
  # Start the scanner in the background, redirecting output to log file
  $CMD > "$SCANNER_LOG" 2>&1 &
  SCANNER_PID=$!
  echo "Scanner started with PID: $SCANNER_PID"
  echo "Log file: $SCANNER_LOG"
  echo "$SCANNER_PID" > .scanner_pid
}

# Function to start the web UI
start_web_ui() {
  if [ "$START_WEB_UI" = true ]; then
    echo "Starting Web UI..."
    python web_ui.py > "$WEB_UI_LOG" 2>&1 &
    WEB_UI_PID=$!
    echo "Web UI started with PID: $WEB_UI_PID"
    echo "Web UI available at: http://127.0.0.1:7777"
    echo "Log file: $WEB_UI_LOG"
    echo "$WEB_UI_PID" > .web_ui_pid
    
    # Open web UI in default browser
    sleep 2 # Wait for the server to start
    if [[ "$OSTYPE" == "darwin"* ]]; then
      open "http://127.0.0.1:7777"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
      xdg-open "http://127.0.0.1:7777"
    fi
  fi
}

# Main execution
check_venv
check_env_file
start_scanner
start_web_ui

echo ""
echo "================================="
echo "Bitcoin News Scanner is running"
echo "================================="
echo "To stop the scanner, run: ./stop_scanner.sh"
echo ""

# Deactivate virtual environment
deactivate
