#!/bin/bash
# Script to stop all instances of the Bitcoin News Scanner Web UI

echo "Stopping all Bitcoin News Scanner Web UI instances..."

# Kill Python web_ui.py processes
pkill -f "python web_ui.py" 2>/dev/null || echo "No web_ui.py processes found."

# Kill any processes listening on common ports used by the app
for port in 5000 7777 8080 9090; do
    pid=$(lsof -i :$port | grep LISTEN | awk '{print $2}' 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "Killing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null
    fi
done

echo "Done!"
echo "You can now restart the web UI with: python web_ui.py"
