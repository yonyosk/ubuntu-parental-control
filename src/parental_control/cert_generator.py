#!/usr/bin/env python3
"""
Certificate Generator - Creates SSL certificates on-the-fly for blocked domains
Signs them with the custom root CA
"""

import logging
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CertificateGenerator:
    """Generates SSL certificates for blocked domains on-the-fly"""

    def __init__(self, ca_cert_path="/opt/ubuntu-parental-control/certs/ca.crt",
                 ca_key_path="/opt/ubuntu-parental-control/certs/ca.key",
                 cert_dir="/opt/ubuntu-parental-control/certs/domains"):
        self.ca_cert_path = Path(ca_cert_path)
        self.ca_key_path = Path(ca_key_path)
        self.cert_dir = Path(cert_dir)

        # Create certificate directory if it doesn't exist
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        # Check if CA exists
        if not self.ca_cert_path.exists() or not self.ca_key_path.exists():
            logger.warning(f"Root CA not found. Run setup_root_ca.sh first.")
            logger.warning(f"HTTPS blocking will not work without root CA.")

    def get_cert_paths(self, domain):
        """Get certificate and key paths for a domain"""
        # Sanitize domain name for filename
        safe_domain = domain.replace('*', 'wildcard').replace('/', '_')
        cert_path = self.cert_dir / f"{safe_domain}.crt"
        key_path = self.cert_dir / f"{safe_domain}.key"
        return cert_path, key_path

    def has_cert(self, domain):
        """Check if certificate already exists for domain"""
        cert_path, key_path = self.get_cert_paths(domain)
        return cert_path.exists() and key_path.exists()

    def generate_cert(self, domain):
        """
        Generate SSL certificate for a specific domain
        Returns (cert_path, key_path) or (None, None) on failure
        """
        try:
            # Check if cert already exists
            if self.has_cert(domain):
                cert_path, key_path = self.get_cert_paths(domain)
                logger.debug(f"Certificate already exists for {domain}")
                return str(cert_path), str(key_path)

            # Check if CA exists
            if not self.ca_cert_path.exists() or not self.ca_key_path.exists():
                logger.error("Root CA not found. Cannot generate certificate.")
                return None, None

            cert_path, key_path = self.get_cert_paths(domain)

            # Generate private key for the domain
            logger.info(f"Generating certificate for {domain}...")
            subprocess.run([
                'openssl', 'genrsa',
                '-out', str(key_path),
                '2048'
            ], check=True, capture_output=True)

            # Create certificate signing request (CSR)
            csr_path = self.cert_dir / f"{domain.replace('*', 'wildcard').replace('/', '_')}.csr"
            subprocess.run([
                'openssl', 'req', '-new',
                '-key', str(key_path),
                '-out', str(csr_path),
                '-subj', f'/CN={domain}'
            ], check=True, capture_output=True)

            # Create certificate config file for SANs (Subject Alternative Names)
            config_path = self.cert_dir / f"{domain.replace('*', 'wildcard').replace('/', '_')}.cnf"
            with open(config_path, 'w') as f:
                f.write(f"""[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = {domain}

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = {domain}
DNS.2 = www.{domain}
""")

            # Sign the certificate with our CA
            subprocess.run([
                'openssl', 'x509', '-req',
                '-in', str(csr_path),
                '-CA', str(self.ca_cert_path),
                '-CAkey', str(self.ca_key_path),
                '-CAcreateserial',
                '-out', str(cert_path),
                '-days', '365',
                '-sha256',
                '-extfile', str(config_path),
                '-extensions', 'v3_req'
            ], check=True, capture_output=True)

            # Clean up temporary files
            csr_path.unlink(missing_ok=True)
            config_path.unlink(missing_ok=True)

            # Set permissions
            os.chmod(key_path, 0o600)
            os.chmod(cert_path, 0o644)

            logger.info(f"Certificate generated for {domain}")
            return str(cert_path), str(key_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate certificate for {domain}: {e}")
            logger.error(f"stderr: {e.stderr.decode() if e.stderr else 'none'}")
            return None, None
        except Exception as e:
            logger.error(f"Error generating certificate for {domain}: {e}")
            return None, None

    def cleanup_old_certs(self, days=30):
        """Remove certificates older than specified days"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            for cert_file in self.cert_dir.glob("*.crt"):
                if cert_file.stat().st_mtime < cutoff.timestamp():
                    key_file = cert_file.with_suffix('.key')
                    cert_file.unlink(missing_ok=True)
                    key_file.unlink(missing_ok=True)
                    logger.info(f"Removed old certificate: {cert_file.name}")
        except Exception as e:
            logger.error(f"Error cleaning up old certificates: {e}")

if __name__ == "__main__":
    # Test certificate generation
    logging.basicConfig(level=logging.INFO)

    gen = CertificateGenerator()
    cert, key = gen.generate_cert("facebook.com")

    if cert and key:
        print(f"Certificate: {cert}")
        print(f"Key: {key}")
    else:
        print("Failed to generate certificate")
