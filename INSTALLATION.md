# Ubuntu Parental Control - Installation Guide

## Quick Start

### First-Time Installation

1. **Clone the repository to your home folder:**
   ```bash
   cd ~
   git clone https://github.com/yonyosk/ubuntu-parental-control.git
   cd ubuntu-parental-control
   ```

2. **Run the installation script:**
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

3. **Access the web interface:**
   - Open your browser to `http://localhost:5000`
   - Or from another computer: `http://<server-ip>:5000`

That's it! The service will:
- ✅ Install to `/opt/ubuntu-parental-control`
- ✅ Set up as a systemd service
- ✅ Start automatically on boot
- ✅ Run securely with proper permissions

---

## Updating to the Latest Version

When new features are released (like the new Category Blocking UI):

1. **Pull the latest changes:**
   ```bash
   cd ~/ubuntu-parental-control
   git pull
   ```

2. **Run the install script again:**
   ```bash
   sudo ./install.sh
   ```

The script will automatically:
- ✅ Stop the service
- ✅ Copy updated files to `/opt`
- ✅ Restart the service
- ✅ Verify new features are installed

**That's it!** No need to manually copy files or worry about paths.

---

## Service Management

### Check service status:
```bash
sudo systemctl status ubuntu-parental-control
```

### View live logs:
```bash
sudo journalctl -u ubuntu-parental-control -f
```

### Restart the service:
```bash
sudo systemctl restart ubuntu-parental-control
```

### Stop the service:
```bash
sudo systemctl stop ubuntu-parental-control
```

### Start the service:
```bash
sudo systemctl start ubuntu-parental-control
```

### Disable auto-start on boot:
```bash
sudo systemctl disable ubuntu-parental-control
```

### Enable auto-start on boot:
```bash
sudo systemctl enable ubuntu-parental-control
```

---

## Troubleshooting

### Changes not showing up after update?

Run the diagnostic script:
```bash
sudo ./verify_installation.sh
```

This will check:
- If new files are installed
- If the service is running the correct version
- If the web interface is accessible
- Recent error logs

### Service won't start?

Check the logs:
```bash
sudo journalctl -u ubuntu-parental-control -n 50 --no-pager
```

Or check the log file directly:
```bash
sudo tail -50 /var/log/ubuntu-parental-control.log
```

### Web interface not accessible?

1. Check if the service is running:
   ```bash
   systemctl is-active ubuntu-parental-control
   ```

2. Check if port 5000 is listening:
   ```bash
   sudo netstat -tlnp | grep 5000
   ```

3. Check firewall rules:
   ```bash
   sudo ufw status
   ```
   If needed, allow port 5000:
   ```bash
   sudo ufw allow 5000/tcp
   ```

---

## File Locations

- **Installation directory:** `/opt/ubuntu-parental-control`
- **Service file:** `/etc/systemd/system/ubuntu-parental-control.service`
- **Configuration:** `/var/lib/ubuntu-parental/control.json`
- **Database:** `/var/lib/ubuntu-parental/control.db`
- **Logs:** `/var/log/ubuntu-parental-control.log`
- **PID file:** `/var/run/ubuntu-parental-control.pid`

---

## Uninstallation

To remove Ubuntu Parental Control:

1. **Stop and disable the service:**
   ```bash
   sudo systemctl stop ubuntu-parental-control
   sudo systemctl disable ubuntu-parental-control
   ```

2. **Remove service file:**
   ```bash
   sudo rm /etc/systemd/system/ubuntu-parental-control.service
   sudo systemctl daemon-reload
   ```

3. **Remove installation directory:**
   ```bash
   sudo rm -rf /opt/ubuntu-parental-control
   ```

4. **Optionally remove data (this deletes all settings and logs):**
   ```bash
   sudo rm -rf /var/lib/ubuntu-parental
   sudo rm -f /var/log/ubuntu-parental-control.log
   sudo rm -f /var/run/ubuntu-parental-control.pid
   ```

5. **Optionally remove the git repository:**
   ```bash
   rm -rf ~/ubuntu-parental-control
   ```

---

## Development vs Production

The `install.sh` script installs to `/opt` which is the recommended approach for both development and production because:

- ✅ **Secure:** Separate from user home directories
- ✅ **Stable:** Survives user account changes
- ✅ **Standard:** Follows Linux best practices
- ✅ **Easy updates:** Just `git pull && sudo ./install.sh`

Your git repository stays in your home folder for easy development, and the install script handles deployment to `/opt`.
