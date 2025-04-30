#!/bin/bash

# Bitcoin News Scanner Stop Script
# This script stops the Bitcoin News Scanner and web UI processes

# Change to the script's directory
cd "$(dirname "$0")"

# Print banner
echo "================================="
echo "  Bitcoin News Scanner Stopper   "
echo "================================="

# Function to stop the scanner
stop_scanner() {
  if [ -f .scanner_pid ]; then
    SCANNER_PID=$(cat .scanner_pid)
    if ps -p "$SCANNER_PID" > /dev/null; then
      echo "Stopping Bitcoin News Scanner (PID: $SCANNER_PID)..."
      kill "$SCANNER_PID"
      rm .scanner_pid
      echo "Scanner stopped"
    else
      echo "Scanner is not running (PID: $SCANNER_PID not found)"
      rm .scanner_pid
    fi
  else
    echo "Scanner PID file not found"
  fi
}

# Function to stop the web UI
stop_web_ui() {
  if [ -f .web_ui_pid ]; then
    WEB_UI_PID=$(cat .web_ui_pid)
    if ps -p "$WEB_UI_PID" > /dev/null; then
      echo "Stopping Web UI (PID: $WEB_UI_PID)..."
      kill "$WEB_UI_PID"
      rm .web_ui_pid
      echo "Web UI stopped"
    else
      echo "Web UI is not running (PID: $WEB_UI_PID not found)"
      rm .web_ui_pid
    fi
  else
    # Try to find and kill any running web_ui.py processes
    echo "Looking for web UI processes..."
    WEB_UI_PIDS=$(pgrep -f "python web_ui.py")
    if [ -n "$WEB_UI_PIDS" ]; then
      echo "Found web UI processes: $WEB_UI_PIDS"
      echo "Stopping processes..."
      for pid in $WEB_UI_PIDS; do
        kill "$pid"
        echo "Stopped process with PID: $pid"
      done
    else
      echo "No web UI processes found"
    fi
  fi
}

# Stop both services
stop_scanner
stop_web_ui

echo ""
echo "================================="
echo "All services stopped"
echo "================================="
