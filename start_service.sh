#!/bin/bash
# Ubuntu Parental Control Service Startup Script

set -e

# Configuration
SERVICE_DIR="/opt/ubuntu-parental-control"
PYTHON_PATH="$SERVICE_DIR/src"
CONFIG_PATH="/var/lib/ubuntu-parental/control.json"
PID_FILE="/var/run/ubuntu-parental-control.pid"
LOG_FILE="/var/log/ubuntu-parental-control.log"

# Ensure directories exist
mkdir -p /var/lib/ubuntu-parental
mkdir -p /var/log
mkdir -p /var/run

# Set up logging
exec 1>> "$LOG_FILE"
exec 2>> "$LOG_FILE"

echo "$(date): Starting Ubuntu Parental Control Service..."

# Change to service directory
cd "$SERVICE_DIR"

# Set Python path
export PYTHONPATH="$PYTHON_PATH:$PYTHONPATH"

# Start the parental control daemon
python3 -c "
import sys
import os
import time
import signal
import logging
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, '$PYTHON_PATH')

from parental_control.parental_control import ParentalControl
from parental_control.web_interface import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('$LOG_FILE'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ubuntu-parental-control')

class ParentalControlDaemon:
    def __init__(self):
        self.pc = None
        self.running = False
        self.web_thread = None
        
    def start_web_interface(self):
        '''Start Flask web interface in a separate thread'''
        try:
            logger.info('Starting Flask web interface...')
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f'Web interface error: {e}')
        
    def start(self):
        try:
            logger.info('Initializing Parental Control...')
            self.pc = ParentalControl()
            
            # Start web interface in background thread
            logger.info('Starting web interface thread...')
            self.web_thread = threading.Thread(target=self.start_web_interface, daemon=True)
            self.web_thread.start()
            
            # Give web interface time to start
            time.sleep(2)
            
            # Start blocking server automatically
            logger.info('Starting blocking server...')
            success = self.pc.start_blocking_server(port=8080)
            if success:
                logger.info('Blocking server started successfully')
            else:
                logger.warning('Failed to start blocking server')
            
            # Write PID file
            with open('$PID_FILE', 'w') as f:
                f.write(str(os.getpid()))
            
            self.running = True
            logger.info('Ubuntu Parental Control Service started successfully')
            logger.info('Web interface available at http://localhost:5000')
            logger.info('Blocking server running on port 8080')
            
            # Keep the service running
            while self.running:
                time.sleep(10)
                # Periodic health check
                if self.pc.blocking_server and not self.pc.blocking_server.is_running():
                    logger.warning('Blocking server stopped unexpectedly, restarting...')
                    self.pc.start_blocking_server(port=8080)
                    
        except Exception as e:
            logger.error(f'Failed to start service: {e}')
            sys.exit(1)
    
    def stop(self):
        logger.info('Stopping Ubuntu Parental Control Service...')
        self.running = False
        if self.pc and self.pc.blocking_server:
            self.pc.stop_blocking_server()
        
        # Remove PID file
        if os.path.exists('$PID_FILE'):
            os.remove('$PID_FILE')
        
        logger.info('Service stopped')

# Signal handlers
daemon = ParentalControlDaemon()

def signal_handler(signum, frame):
    daemon.stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Start the daemon
daemon.start()
" &

# Get the background process PID and save it
echo $! > "$PID_FILE"

echo "$(date): Ubuntu Parental Control Service started with PID $(cat $PID_FILE)"
