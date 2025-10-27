#!/usr/bin/env python3
"""
Blocking Server - Intercepts blocked requests and serves friendly block pages
"""

import logging
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class BlockingHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves block pages for blocked domains"""
    
    def __init__(self, *args, parental_control=None, **kwargs):
        self.parental_control = parental_control
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Parse the requested URL
            parsed_url = urlparse(self.path)
            host = self.headers.get('Host', 'unknown')
            
            # Check if this domain should be blocked
            if self.parental_control:
                is_blocked, categories = self.parental_control.is_domain_blocked(host)
                is_allowed, reason = self.parental_control.is_access_allowed(domain=host)
                
                if not is_allowed or is_blocked:
                    self.serve_block_page(host, reason, categories)
                    return
            
            # If not blocked, serve a simple redirect or error
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Page Not Found</h1></body></html>')
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, "Internal Server Error")
    
    def do_POST(self):
        """Handle POST requests (same as GET for blocking)"""
        self.do_GET()
    
    def serve_block_page(self, blocked_url, reason, categories):
        """Serve the friendly block page"""
        try:
            # Determine block category and reason
            block_category = categories[0] if categories else 'MANUAL'
            
            # Create block page URL with parameters
            block_url = f"http://localhost:5000/blocked"
            params = {
                'url': blocked_url,
                'reason': reason,
                'category': block_category
            }
            
            # Add time restriction info if applicable
            if 'schedule' in reason.lower() or 'time' in reason.lower():
                params['time_restriction'] = reason
            
            # Build query string
            query_params = '&'.join([f"{k}={quote(str(v))}" for k, v in params.items()])
            redirect_url = f"{block_url}?{query_params}"
            
            # Send redirect to block page
            self.send_response(302)
            self.send_header('Location', redirect_url)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Also send a simple HTML response in case redirect doesn't work
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Page Blocked</title>
                <meta http-equiv="refresh" content="0;url={redirect_url}">
            </head>
            <body>
                <h1>Page Blocked</h1>
                <p>This page has been blocked by parental control.</p>
                <p><a href="{redirect_url}">Click here if you are not redirected automatically</a></p>
            </body>
            </html>
            """
            self.wfile.write(html_content.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Error serving block page: {e}")
            self.send_error(500, "Error serving block page")
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"BlockingServer: {format % args}")

class BlockingServer:
    """HTTP server that intercepts blocked requests"""
    
    def __init__(self, parental_control, port=8080):
        self.parental_control = parental_control
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
    
    def start(self):
        """Start the blocking server"""
        try:
            # Create handler class with parental_control instance
            def handler_factory(*args, **kwargs):
                return BlockingHandler(*args, parental_control=self.parental_control, **kwargs)
            
            # Create and start server
            self.server = HTTPServer(('127.0.0.1', self.port), handler_factory)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            self.running = True
            
            logger.info(f"Blocking server started on port {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start blocking server: {e}")
            return False
    
    def stop(self):
        """Stop the blocking server"""
        if self.server and self.running:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            logger.info("Blocking server stopped")
    
    def is_running(self):
        """Check if server is running"""
        return self.running and self.server_thread and self.server_thread.is_alive()

def update_hosts_file_for_blocking_server(parental_control, server_port=8080):
    """Update hosts file to redirect blocked domains to local blocking server"""
    try:
        # Get all blocked domains
        blocked_sites = parental_control.db.get_blocked_sites()
        blocked_domains = [site['domain'] for site in blocked_sites]
        
        # Get blacklist domains (sample - this could be expensive for large lists)
        # For now, just get manually blocked sites
        
        # Read current hosts file
        hosts_path = Path('/etc/hosts')
        if not hosts_path.exists():
            logger.error("Hosts file not found")
            return False
        
        with open(hosts_path, 'r') as f:
            hosts_content = f.read()
        
        # Remove old parental control entries
        lines = hosts_content.split('\n')
        new_lines = []
        in_parental_section = False
        
        for line in lines:
            if '# Ubuntu Parental Control - START' in line:
                in_parental_section = True
                continue
            elif '# Ubuntu Parental Control - END' in line:
                in_parental_section = False
                continue
            elif not in_parental_section:
                new_lines.append(line)
        
        # Add new parental control entries
        new_lines.append('')
        new_lines.append('# Ubuntu Parental Control - START')
        new_lines.append('# Blocked domains redirect to local blocking server')
        
        for domain in blocked_domains:
            new_lines.append(f'127.0.0.1\t{domain}')
            new_lines.append(f'127.0.0.1\twww.{domain}')
        
        new_lines.append('# Ubuntu Parental Control - END')
        new_lines.append('')
        
        # Write updated hosts file
        new_content = '\n'.join(new_lines)
        with open(hosts_path, 'w') as f:
            f.write(new_content)
        
        logger.info(f"Updated hosts file with {len(blocked_domains)} blocked domains")
        return True
        
    except Exception as e:
        logger.error(f"Error updating hosts file: {e}")
        return False

if __name__ == "__main__":
    # Test the blocking server
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    
    from parental_control import ParentalControl
    
    logging.basicConfig(level=logging.INFO)
    
    pc = ParentalControl()
    server = BlockingServer(pc, port=8080)
    
    try:
        if server.start():
            print("Blocking server started. Press Ctrl+C to stop.")
            while True:
                import time
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
