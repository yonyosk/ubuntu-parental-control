#!/usr/bin/env python3
"""
Blocking Server - Intercepts blocked requests and serves friendly block pages
Supports both HTTP and HTTPS with dynamic certificate generation
"""

import logging
import socket
import ssl
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

            # Detect if this was originally an HTTPS request
            # When iptables redirects port 443 to 8080, we can infer HTTPS intent
            # by checking if the connection came through certain mechanisms
            was_https = self._is_https_request()

            # Check if this domain should be blocked
            if self.parental_control:
                is_blocked, categories = self.parental_control.is_domain_blocked(host)
                is_allowed, reason = self.parental_control.is_access_allowed(domain=host)

                if not is_allowed or is_blocked:
                    self.serve_block_page(host, reason, categories, was_https=was_https)
                    return

            # If not blocked, serve a simple redirect or error
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Page Not Found</h1></body></html>')

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, "Internal Server Error")

    def _is_https_request(self):
        """
        Detect if the request was originally intended for HTTPS.
        This is a heuristic since we're receiving redirected traffic.
        """
        # Check for common HTTPS indicators in headers
        # Some browsers send Upgrade-Insecure-Requests for HTTPS
        if self.headers.get('Upgrade-Insecure-Requests') == '1':
            return True

        # Check if the referrer is HTTPS
        referrer = self.headers.get('Referer', '')
        if referrer.startswith('https://'):
            return True

        # Default to HTTP (most conservative approach)
        return False
    
    def do_POST(self):
        """Handle POST requests (same as GET for blocking)"""
        self.do_GET()
    
    def serve_block_page(self, blocked_url, reason, categories, was_https=False):
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

            # Add HTTPS indicator if detected
            if was_https:
                params['was_https'] = 'true'

            # Build query string
            query_params = '&'.join([f"{k}={quote(str(v))}" for k, v in params.items()])
            redirect_url = f"{block_url}?{query_params}"

            # Send redirect to block page
            self.send_response(302)
            self.send_header('Location', redirect_url)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Also send a simple HTML response in case redirect doesn't work
            https_note = " (HTTPS)" if was_https else ""
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Page Blocked</title>
                <meta http-equiv="refresh" content="0;url={redirect_url}">
            </head>
            <body>
                <h1>Page Blocked{https_note}</h1>
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
    """HTTP/HTTPS server that intercepts blocked requests"""

    def __init__(self, parental_control, port=8080, https_port=8443, use_https=True):
        self.parental_control = parental_control
        self.port = port
        self.https_port = https_port
        self.use_https = use_https
        self.http_server = None
        self.https_server = None
        self.http_thread = None
        self.https_thread = None
        self.running = False
        self.cert_generator = None

        # Initialize certificate generator if HTTPS is enabled
        if self.use_https:
            try:
                from parental_control.cert_generator import CertificateGenerator
                self.cert_generator = CertificateGenerator()
            except Exception as e:
                logger.warning(f"Failed to initialize certificate generator: {e}")
                logger.warning("HTTPS blocking will not be available")
                self.use_https = False

    def _sni_callback(self, ssl_socket, server_name, ssl_context):
        """SNI callback to load the correct certificate for the requested domain"""
        try:
            if server_name and self.cert_generator:
                # Generate or get certificate for this domain
                cert_path, key_path = self.cert_generator.generate_cert(server_name)

                if cert_path and key_path:
                    # Create new SSL context with domain-specific certificate
                    new_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    new_context.load_cert_chain(cert_path, key_path)
                    ssl_socket.context = new_context
                    logger.debug(f"Loaded certificate for {server_name}")
                else:
                    logger.warning(f"Failed to generate certificate for {server_name}")
        except Exception as e:
            logger.error(f"SNI callback error for {server_name}: {e}")

    def start(self):
        """Start the blocking server (HTTP and optionally HTTPS)"""
        try:
            # Create handler class with parental_control instance
            def handler_factory(*args, **kwargs):
                return BlockingHandler(*args, parental_control=self.parental_control, **kwargs)

            # Start HTTP server
            self.http_server = HTTPServer(('127.0.0.1', self.port), handler_factory)
            self.http_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
            self.http_thread.start()
            logger.info(f"HTTP blocking server started on port {self.port}")

            # Start HTTPS server if enabled and CA is available
            if self.use_https and self.cert_generator:
                ca_cert = Path("/opt/ubuntu-parental-control/certs/ca.crt")
                ca_key = Path("/opt/ubuntu-parental-control/certs/ca.key")

                if ca_cert.exists() and ca_key.exists():
                    self.https_server = HTTPServer(('127.0.0.1', self.https_port), handler_factory)

                    # Create SSL context with SNI support
                    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

                    # Load CA certificate as default
                    ssl_context.load_cert_chain(str(ca_cert), str(ca_key))

                    # Set SNI callback for domain-specific certificates
                    ssl_context.sni_callback = self._sni_callback

                    # Wrap socket with SSL
                    self.https_server.socket = ssl_context.wrap_socket(
                        self.https_server.socket,
                        server_side=True
                    )

                    self.https_thread = threading.Thread(target=self.https_server.serve_forever, daemon=True)
                    self.https_thread.start()
                    logger.info(f"HTTPS blocking server started on port {self.https_port}")
                else:
                    logger.warning("Root CA not found. HTTPS blocking disabled.")
                    logger.warning("Run: sudo ./setup_root_ca.sh")

            self.running = True
            return True

        except Exception as e:
            logger.error(f"Failed to start blocking server: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def stop(self):
        """Stop the blocking server"""
        if self.http_server and self.running:
            self.http_server.shutdown()
            self.http_server.server_close()
            logger.info("HTTP blocking server stopped")

        if self.https_server and self.running:
            self.https_server.shutdown()
            self.https_server.server_close()
            logger.info("HTTPS blocking server stopped")

        self.running = False

    def is_running(self):
        """Check if server is running"""
        http_running = self.http_thread and self.http_thread.is_alive()
        https_running = self.https_thread and self.https_thread.is_alive() if self.use_https else True
        return self.running and http_running

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
