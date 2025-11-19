# Ubuntu Parental Control

## Overview
Ubuntu Parental Control is a comprehensive web-based application that allows parents to manage and monitor internet access for their children. With an intuitive interface and powerful features, it helps create a safer online environment for families.

> **Note**: A Windows version is currently in development. See the [Windows Port Documentation](docs/windows-port/) for details.

## Key Features

### Content Filtering
- Block websites by domain or wildcard patterns
- Block website categories using external blacklists (UT1)
- Support for custom block/allow lists
- Real-time domain blocking using hosts file
- **Friendly blocking pages** - Custom Hebrew/English blocking pages instead of connection errors
- **HTTPS blocking support** - Seamless blocking with dynamic SSL certificate generation

### Time Management
- Set daily internet usage limits
- Create flexible access schedules by day of week
- Temporary access exceptions
- Usage tracking and notifications

### DNS Protection
- Configurable DNS settings (OpenDNS, Cloudflare Family, etc.)
- Automatic DNS-based content filtering
- Custom DNS server support

### Activity Monitoring & Reporting
- Detailed activity logs (allowed/blocked sites)
- Usage statistics and trends
- Exportable reports (CSV)
- Real-time monitoring dashboard

### Security
- Secure web interface with password protection
- Automatic HTTPS support
- Audit logging of all administrative actions
- Role-based access control

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or later (64-bit)
- Python 3.8 or higher
- pip (Python package manager)
- systemd (for service management)
- Root/sudo access (for system integration)

### Recommended Hardware
- 1 GHz or faster processor
- 1 GB RAM (2 GB recommended)
- 200 MB available disk space
- Network connectivity

## Installation

### Quick Installation (Recommended)

This is the easiest method and sets up everything automatically, including HTTPS blocking with certificate management.

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ubuntu-parental-control.git
cd ubuntu-parental-control
```

2. Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y python3 openssl iptables rsync
```

3. Run the installation script:
```bash
sudo ./install_service.sh
```

The installation script will automatically:
- Remove conflicting packages
- Set up a custom root CA certificate for HTTPS blocking
- Install the service to `/opt/ubuntu-parental-control`
- Configure systemd service to start on boot
- Set up iptables rules for port redirection
- Install iptables-persistent (optional, for persistence across reboots)
- Start the service

**Installation time**: ~5 seconds on subsequent installs (first install may take 30 seconds due to package downloads)

### HTTPS Blocking Setup (Optional for Firefox Users)

For seamless HTTPS blocking without certificate warnings in Firefox:

1. Open Firefox → Settings → Privacy & Security → Certificates
2. Click "View Certificates" → "Authorities" → "Import"
3. Select: `/opt/ubuntu-parental-control/certs/ca.crt`
4. Check "Trust this CA to identify websites"
5. Click OK

**Note**: Chrome and other browsers that use the system certificate store will work automatically without this step.

### Verify Installation

Check that the service is running:
```bash
sudo systemctl status ubuntu-parental-control
```

Access the admin panel at: http://localhost:5000

Test blocking (if you have blocked sites configured):
```bash
# HTTP blocking
curl http://facebook.com

# HTTPS blocking (should work without SSL errors after CA setup)
curl https://facebook.com
```

## Upgrading

To upgrade to the latest version:

```bash
cd ubuntu-parental-control
git pull origin main
sudo ./install_service.sh
```

The installation script will:
- Preserve your existing root CA certificate (if present)
- Update the service code
- Restart the service with the new version
- Keep your database and settings intact

## Getting Started

### First-Time Setup

1. Access the web interface at `https://localhost:5000` (HTTPS is enabled by default)
2. Set up your administrator account with a strong password
3. Configure your network settings (DNS, proxy if needed)
4. Set up content filtering rules and time restrictions
5. Review the dashboard for activity monitoring

### Quick Start Guide

#### Blocking Websites
1. Navigate to "Content Filtering"
2. Select categories to block or add custom domains
3. Click "Save Changes" to apply immediately

#### Setting Time Limits
1. Go to "Time Management"
2. Add a new schedule or set daily usage limits
3. Configure allowed hours for each day of the week

#### Viewing Reports
1. Click on "Reports" in the navigation
2. Use filters to view specific time periods or activities
3. Export reports as needed for record-keeping

## Uninstallation

### For Direct Installation:
```bash
# Stop the service if running
pkill -f ubuntu-parental-web

# Uninstall the package
pip uninstall ubuntu-parental-control

# Remove configuration files (optional)
rm -rf ~/.config/ubuntu-parental
```

### For Debian Package:
```bash
# Stop and disable the service
sudo systemctl stop ubuntu-parental-web
sudo systemctl disable ubuntu-parental-web

# Remove the package
sudo dpkg -r ubuntu-parental-control

# Remove configuration files (optional)
sudo rm -rf /etc/ubuntu-parental
```

## Security Best Practices

### Access Control
- Use a strong, unique password for the admin account
- Enable HTTPS in production environments
- Regularly update the software to get security patches
- Restrict access to the web interface using firewall rules

### Monitoring
- Review activity logs regularly
- Set up email alerts for suspicious activities
- Monitor disk space for log files

## Troubleshooting

### Common Issues

#### Web Interface Not Accessible
```bash
# Check if the service is running
sudo systemctl status ubuntu-parental-web

# Check logs for errors
journalctl -u ubuntu-parental-web -n 50 --no-pager
```

#### Websites Not Being Blocked
1. Verify the domain is in the block list
2. Check if the hosts file has been updated
3. Clear the DNS cache:
   ```bash
   sudo systemd-resolve --flush-caches
   ```

#### High CPU/Memory Usage
- Check for excessive logging
- Review scheduled tasks
- Consider increasing system resources if needed

## Performance Tuning

### Database Optimization
```bash
# Optimize the SQLite database (run during low-usage periods)
sqlite3 /var/lib/ubuntu-parental/control.db "VACUUM;"
```

### Log Rotation
Configure log rotation in `/etc/logrotate.d/ubuntu-parental`:
```
/var/log/ubuntu-parental/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 root adm
    sharedscripts
    postrotate
        systemctl reload ubuntu-parental-web > /dev/null
    endscript
}
```

## Documentation

### Project Documentation

This project includes comprehensive documentation for various aspects:

#### Core Documentation
- **[User Guide](docs/user/)** - Installation and usage instructions
- **[API Documentation](docs/api/)** - RESTful API reference

#### Platform-Specific Documentation
- **[Windows Port](docs/windows-port/)** - Windows version development
  - [Product Requirements Document (PRD)](docs/windows-port/PRD.md) - Complete product specification
  - [Architecture Document](docs/windows-port/ARCHITECTURE.md) - Technical architecture and design
  - [Task List](docs/windows-port/TASK_LIST.md) - Development roadmap and tasks

#### Feature Documentation
- **[Blocking Page Feature](docs/features/blocking-page/)** - Custom blocking page implementation
  - [Project Overview](docs/features/blocking-page/01_project_overview.md)
  - [Technical Architecture](docs/features/blocking-page/02_technical_architecture.md)
  - [Design Specifications](docs/features/blocking-page/03_design_specifications.md)
  - [Development Roadmap](docs/features/blocking-page/04_development_roadmap.md)
  - [Database Schema](docs/features/blocking-page/05_database_schema.md)
  - [Risk Mitigation](docs/features/blocking-page/06_risk_mitigation.md)
- **[HTTPS Blocking Setup](docs/HTTPS_BLOCKING.md)** - Configure HTTPS blocking with dynamic certificates

### API Documentation

The web interface provides a RESTful API for programmatic access. API documentation is available at `/api/docs` when the application is running.

#### Example: Get Current Usage

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     https://localhost:5000/api/time/usage
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with debug mode
FLASK_DEBUG=1 FLASK_APP=parental_control.web_interface:app flask run
```

## Support

For support, please:
1. Check the [Wiki](https://github.com/YOUR_USERNAME/ubuntu-parental-control/wiki)
2. Search existing issues
3. Open a new issue with detailed information

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- Built with Flask and SQLite
- Uses OpenDNS for DNS-based filtering
- Inspired by various open-source parental control solutions
