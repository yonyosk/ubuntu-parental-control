#!/bin/bash
# Ubuntu Parental Control Service Stop Script

set -e

# Configuration
PID_FILE="/var/run/ubuntu-parental-control.pid"
LOG_FILE="/var/log/ubuntu-parental-control.log"

echo "$(date): Stopping Ubuntu Parental Control Service..." >> "$LOG_FILE"

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    
    # Check if process is running
    if kill -0 "$PID" 2>/dev/null; then
        echo "$(date): Sending TERM signal to process $PID..." >> "$LOG_FILE"
        kill -TERM "$PID"
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                echo "$(date): Process stopped gracefully" >> "$LOG_FILE"
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 "$PID" 2>/dev/null; then
            echo "$(date): Force killing process $PID..." >> "$LOG_FILE"
            kill -KILL "$PID"
        fi
    else
        echo "$(date): Process $PID not running" >> "$LOG_FILE"
    fi
    
    # Remove PID file
    rm -f "$PID_FILE"
else
    echo "$(date): PID file not found" >> "$LOG_FILE"
fi

echo "$(date): Ubuntu Parental Control Service stopped" >> "$LOG_FILE"
