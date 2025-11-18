from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from functools import wraps
import secrets
import datetime
import os
import sys
import logging
import time as time_module
from pathlib import Path
import subprocess
try:
    from flask_wtf.csrf import CSRFProtect
except ImportError:
    CSRFProtect = None  # CSRF protection will be optional if flask-wtf not installed

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Handle both relative and absolute imports
try:
    from .parental_control import ParentalControl, WebsiteCategory
    from .database import ParentalControlDB
    from .validation import InputValidator, ValidationError
except ImportError:
    from parental_control.parental_control import ParentalControl, WebsiteCategory
    from parental_control.database import ParentalControlDB
    from parental_control.validation import InputValidator, ValidationError
import csv
import io
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union

print("Starting web interface...")  # Debug print

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/ubuntu-parental/web.log')
    ]
)

logging.info("Initializing application...")

# Add the src directory to Python path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    try:
        from .parental_control import ParentalControl, WebsiteCategory
        from .database import ParentalControlDB
    except ImportError:
        from parental_control.parental_control import ParentalControl, WebsiteCategory
        from parental_control.database import ParentalControlDB
    logging.info("Successfully imported modules")
except Exception as e:
    logging.error(f"Import error: {str(e)}")
    raise

app = Flask(__name__)

# Use a persistent secret key to avoid session invalidation on restart
SECRET_KEY_FILE = '/var/lib/ubuntu-parental/flask_secret.key'
try:
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, 'r') as f:
            app.secret_key = f.read().strip()
    else:
        # Generate new secret key and save it
        app.secret_key = secrets.token_hex(32)
        os.makedirs(os.path.dirname(SECRET_KEY_FILE), exist_ok=True)
        with open(SECRET_KEY_FILE, 'w') as f:
            f.write(app.secret_key)
        os.chmod(SECRET_KEY_FILE, 0o600)  # Secure file permissions
except Exception as e:
    logging.warning(f"Could not persist secret key: {e}, using temporary key")
    app.secret_key = secrets.token_hex(32)

# Configure session for better reliability
app.config.update(
    SESSION_COOKIE_SECURE=False,  # Set to True if using HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=14400,  # 4 hours in seconds
)

# Enable CSRF protection if flask-wtf is available
if CSRFProtect:
    csrf = CSRFProtect(app)
    logging.info("CSRF protection enabled")
else:
    logging.warning("flask-wtf not available - CSRF protection disabled")

# Define the path to the database
DB_PATH = Path('/var/lib/ubuntu-parental/control.json')
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Add custom Jinja2 filters
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime string for display in templates."""
    if not value:
        return ''

    try:
        # If value is already a datetime object
        if hasattr(value, 'strftime'):
            return value.strftime(format)

        # If value is a string, parse it first
        if isinstance(value, str):
            # Try to parse ISO format datetime string
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime(format)
            except ValueError:
                # If parsing fails, return the original value
                return value

        return str(value)
    except Exception as e:
        logging.error(f"Error formatting datetime {value}: {e}")
        return str(value)

@app.template_filter('is_schedule_active_now')
def is_schedule_active_now(schedule):
    """Check if a schedule is currently active based on time and day."""
    try:
        if not schedule or not schedule.get('is_active'):
            return False

        now = datetime.now()
        current_time = now.time()
        current_day = now.weekday()  # Monday=0, Sunday=6

        # Check if current day is in the schedule's days
        days = schedule.get('days', [])
        if current_day not in days:
            return False

        # Parse start and end times
        start_time_str = schedule.get('start_time', '')
        end_time_str = schedule.get('end_time', '')

        if not start_time_str or not end_time_str:
            return False

        # Parse time strings (expected format: "HH:MM" or "HH:MM:SS")
        start_parts = start_time_str.split(':')
        end_parts = end_time_str.split(':')

        start_time = datetime.strptime(start_time_str, '%H:%M' if len(start_parts) == 2 else '%H:%M:%S').time()
        end_time = datetime.strptime(end_time_str, '%H:%M' if len(end_parts) == 2 else '%H:%M:%S').time()

        # Check if current time is within the schedule
        if start_time <= end_time:
            # Normal case: start time is before end time (e.g., 9:00 to 17:00)
            return start_time <= current_time <= end_time
        else:
            # Crosses midnight (e.g., 22:00 to 02:00)
            return current_time >= start_time or current_time <= end_time

    except Exception as e:
        logging.error(f"Error checking if schedule is active: {e}")
        return False

logging.info("Flask app created")

# Simple rate limiting for login attempts
login_attempts = {}  # IP -> {'count': int, 'last_attempt': timestamp}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes

def check_rate_limit(ip_address):
    """Check if IP is rate limited for login attempts."""
    current_time = time_module.time()
    
    if ip_address not in login_attempts:
        return True
    
    attempt_data = login_attempts[ip_address]
    
    # Reset counter if lockout period has passed
    if current_time - attempt_data['last_attempt'] > LOCKOUT_DURATION:
        login_attempts[ip_address] = {'count': 0, 'last_attempt': current_time}
        return True
    
    # Check if too many attempts
    if attempt_data['count'] >= MAX_LOGIN_ATTEMPTS:
        return False
    
    return True

def record_login_attempt(ip_address, success=False):
    """Record a login attempt."""
    current_time = time_module.time()
    
    if success:
        # Clear attempts on successful login
        if ip_address in login_attempts:
            del login_attempts[ip_address]
    else:
        # Increment failed attempts
        if ip_address not in login_attempts:
            login_attempts[ip_address] = {'count': 1, 'last_attempt': current_time}
        else:
            login_attempts[ip_address]['count'] += 1
            login_attempts[ip_address]['last_attempt'] = current_time

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    # Prevent XSS attacks
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy (allow required CDNs for styling)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-src 'none'; "
        "object-src 'none'"
    )
    
    # Prevent caching of sensitive pages
    if request.endpoint != 'static':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

def get_db_connection():
    """Get database connection using new TinyDB layer"""
    try:
        return ParentalControlDB(str(DB_PATH))
    except Exception as e:
        logging.error(f"Database connection error: {str(e)}")
        raise

def login_required(f):
    """Decorator that requires valid authentication to access protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if user is logged in
            logging.debug(f"login_required: checking session {dict(session)}")
            if not session.get('logged_in'):
                logging.debug("Session not logged in, redirecting to login")
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('login'))

            # Check if session has login_time
            if 'login_time' not in session:
                logging.warning("Session missing login_time, clearing session")
                session.clear()
                flash('Invalid session. Please log in again', 'warning')
                return redirect(url_for('login'))

            # Check if session is still valid (timeout check)
            session_age = time_module.time() - session['login_time']
            if session_age > 14400:  # 4 hours
                logging.info(f"Session expired after {session_age} seconds")
                session.clear()
                flash('Session expired. Please log in again', 'info')
                return redirect(url_for('login'))

            logging.debug(f"Session valid, age: {session_age} seconds")
            return f(*args, **kwargs)

        except Exception as e:
            logging.error(f"Error in login_required decorator: {e}")
            session.clear()
            flash('Authentication error. Please log in again', 'danger')
            return redirect(url_for('login'))
    return decorated_function



@app.route('/')
@login_required
def index():
    try:
        logging.info("Accessing index page")
        db = get_db_connection()
        
        # Get blocked sites and count
        blocked_sites = db.get_blocked_sites()
        blocked_count = len(blocked_sites)
        
        # Get active temporary exceptions
        temp_exceptions = db.get_active_exceptions()
        
        # Get categories for blocking
        categories = list(WebsiteCategory.__dict__.keys())
        # Filter out private attributes and methods
        categories = [cat for cat in categories if not cat.startswith('_')]
        
        # Get blocked categories
        blocked_categories = list(set([site['category'] for site in blocked_sites if site.get('category')]))
        
        # Get today's usage and blocks
        today = datetime.now().strftime('%Y-%m-%d')
        today_usage_data = db.get_daily_usage(today)
        today_usage = today_usage_data.get('minutes_used', 0)
        
        # Get today's activity logs for blocks count
        today_logs = db.get_activity_logs(start_date=today, end_date=today, action='blocked')
        today_blocks = len(today_logs)
        
        # Get active schedules
        active_schedules = db.get_time_schedules(active_only=True)
        
        # Get recent activity
        recent_activity = db.get_activity_logs(limit=5)
        
        # Get daily limit
        settings = db.get_settings()
        daily_limit = settings.get('daily_limit_minutes')
        
        db.close()
        
        # Check if protection is active
        pc = ParentalControl()
        is_protection_active = pc.is_protection_active() if pc else False
        
        return render_template('index.html', 
                             blocked_sites=blocked_sites,
                             temp_exceptions=temp_exceptions,
                             categories=categories,
                             blocked_categories=blocked_categories,
                             blocked_count=blocked_count,
                             today_usage=today_usage,
                             today_blocks=today_blocks,
                             active_schedules=active_schedules,
                             recent_activity=recent_activity,
                             daily_limit=daily_limit,
                             is_protection_active=is_protection_active,
                             current_page='dashboard')
    except Exception as e:
        logging.error(f"Error in index route: {str(e)}")
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
        
        # If already logged in, redirect to dashboard
        if session.get('logged_in'):
            logging.debug(f"User already logged in, session data: {dict(session)}")
            # Verify session is actually valid before redirecting
            if 'login_time' in session:
                session_age = time_module.time() - session['login_time']
                if session_age < 14400:  # Less than 4 hours
                    logging.info("Valid existing session found, redirecting to index")
                    return redirect(url_for('index'))
                else:
                    logging.info("Existing session expired, clearing")
                    session.clear()
            else:
                logging.warning("Session logged_in but missing login_time, clearing")
                session.clear()
            
        if request.method == 'POST':
            # Check rate limiting
            if not check_rate_limit(client_ip):
                remaining_time = LOCKOUT_DURATION - (time_module.time() - login_attempts[client_ip]['last_attempt'])
                flash(f'Too many login attempts. Please try again in {int(remaining_time/60)} minutes.', 'danger')
                return render_template('login.html')
            
            password = request.form.get('password', '').strip()
            
            if not password:
                flash('Password is required', 'danger')
                return render_template('login.html')
            
            # Validate password input
            try:
                password = InputValidator.sanitize_string(password, max_length=128)
            except ValidationError as e:
                record_login_attempt(client_ip, success=False)
                flash(f'Invalid password format: {str(e)}', 'danger')
                return render_template('login.html')
            
            logging.info(f"Login attempt from {client_ip}")
            control = ParentalControl()
            
            # Check if password is set up
            try:
                password_is_set = control.has_password_set()
            except Exception as e:
                # Database access error - don't allow login
                record_login_attempt(client_ip, success=False)
                flash('System error: Unable to access user database. Please check system permissions.', 'danger')
                logging.error(f"Database access error during login from {client_ip}: {e}")
                return render_template('login.html')
            
            if not password_is_set:
                # First-time setup - set the password
                if len(password) < 4:
                    record_login_attempt(client_ip, success=False)
                    flash('Password must be at least 4 characters for initial setup', 'danger')
                    return render_template('login.html', setup_mode=True)
                
                if control.set_password(password):
                    session['logged_in'] = True
                    session['login_time'] = time_module.time()
                    record_login_attempt(client_ip, success=True)
                    flash('Password set successfully! Welcome to Ubuntu Parental Control', 'success')
                    logging.info(f"Initial password setup completed from {client_ip}")
                    return redirect(url_for('index'))
                else:
                    record_login_attempt(client_ip, success=False)
                    flash('Failed to set up password. Please try again', 'danger')
                    return render_template('login.html', setup_mode=True)
            else:
                # Normal login
                if control.verify_password(password):
                    session.permanent = True
                    session['logged_in'] = True
                    session['login_time'] = time_module.time()
                    record_login_attempt(client_ip, success=True)
                    logging.info(f"Login successful from {client_ip}, session data: {dict(session)}")
                    flash('Welcome back!', 'success')
                    return redirect(url_for('index'))
                else:
                    record_login_attempt(client_ip, success=False)
                    logging.warning(f"Invalid login attempt from {client_ip}")
                    flash('Invalid password', 'danger')
                    
        else:
            # GET request - check if setup mode
            control = ParentalControl()
            try:
                setup_mode = not control.has_password_set()
            except Exception as e:
                # Database access error - assume normal login mode
                logging.error(f"Database access error checking setup mode: {e}")
                setup_mode = False
            return render_template('login.html', setup_mode=setup_mode)
            
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        flash(f"An error occurred during login: {str(e)}", 'danger')
        
    return render_template('login.html')

@app.route('/block_site', methods=['POST'])
@login_required
def block_site():
    try:
        domain = request.form.get('domain', '').strip()
        if not domain:
            flash('Domain cannot be empty', 'danger')
            return redirect(url_for('index'))
        
        logging.info(f"Attempting to block domain: {domain}")
        
        control = ParentalControl()
        success = control.add_blocked_site(domain)
        
        if success:
            flash(f'Successfully blocked {domain}', 'success')
            logging.info(f"Successfully blocked domain: {domain}")
        else:
            flash(f'Failed to block {domain}', 'warning')
            logging.warning(f"Failed to block domain: {domain}")
    except Exception as e:
        logging.error(f"Error blocking site: {str(e)}")
        flash(f'Error blocking site: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/block_category', methods=['POST'])
@login_required
def block_category():
    try:
        category_name = request.form.get('category', '').strip()
        if not category_name:
            flash('Category cannot be empty', 'danger')
            return redirect(url_for('index'))
            
        logging.info(f"Attempting to block category: {category_name}")
        
        control = ParentalControl()
        
        category_map = {
            'SOCIAL_MEDIA': WebsiteCategory.SOCIAL_MEDIA,
            'GAMING': WebsiteCategory.GAMING,
            'VIDEO': WebsiteCategory.VIDEO
        }
        
        if category_name in category_map:
            control.block_category(category_map[category_name])
            flash(f'Successfully blocked {category_name} category', 'success')
            logging.info(f"Successfully blocked category: {category_name}")
        else:
            logging.warning(f"Invalid category name: {category_name}")
            flash('Invalid category', 'warning')
    except Exception as e:
        logging.error(f"Error blocking category: {str(e)}")
        flash(f'Error blocking category: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/unblock_site', methods=['POST'])
@login_required
def unblock_site():
    try:
        domain = request.form.get('domain', '').strip()
        duration = request.form.get('duration', type=int)
        
        if not domain:
            flash('Domain cannot be empty', 'danger')
            return redirect(url_for('index'))
        
        if duration is None or duration <= 0:
            flash('Duration must be a positive number', 'danger')
            return redirect(url_for('index'))
            
        logging.info(f"Attempting to unblock {domain} for {duration} minutes")
        
        control = ParentalControl()
        # Pass empty string for password since auth is disabled
        if control.temporarily_unblock(domain, duration, ""):
            flash(f'Successfully unblocked {domain} for {duration} minutes', 'success')
            logging.info(f"Successfully unblocked {domain}")
        else:
            flash('Failed to unblock site', 'warning')
            logging.error(f"Failed to unblock {domain}")
    except Exception as e:
        logging.error(f"Error unblocking site: {str(e)}")
        flash(f'Error unblocking site: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/unblock_all_sites', methods=['POST'])
@login_required
def unblock_all_sites():
    try:
        duration = int(request.form.get('duration', 30))  # Default 30 minutes
        logging.info(f"Attempting to unblock all sites for {duration} minutes")
        
        control = ParentalControl()
        conn = get_db_connection()
        
        # Get all blocked domains using the database connection
        blocked_sites = conn.get_blocked_sites()
        domains = [site['domain'] for site in blocked_sites]
        success_count = 0
        
        # Unblock each domain
        for domain in domains:
            if control.temporarily_unblock(domain, duration, ""):  # Empty password since auth is session-based
                success_count += 1
                # Log the action
                conn.log_activity(
                    domain=domain,
                    action="unblocked_all",
                    details={"duration_minutes": duration, "reason": "Bulk unblock from dashboard"}
                )
        
        conn.close()
        
        if success_count > 0:
            flash(f'Successfully unblocked {success_count} sites for {duration} minutes', 'success')
            logging.info(f"Successfully unblocked {success_count} sites")
        else:
            flash('No sites were unblocked', 'warning')
            
    except Exception as e:
        logging.error(f"Error unblocking all sites: {str(e)}")
        flash(f'Error unblocking sites: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/dns_settings', methods=['GET'])
@login_required
def dns_settings():
    """Display and update DNS settings"""
    try:
        control = ParentalControl()
        current_settings = control.get_dns_settings()
        return render_template('dns_settings.html', 
                            current_settings=current_settings,
                            current_page='dns_settings')
    except Exception as e:
        logging.error(f"Error in DNS settings: {str(e)}")
        flash(f"Error accessing DNS settings: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/update_dns_settings', methods=['POST'])
@login_required
def update_dns_settings():
    """Update DNS settings"""
    try:
        control = ParentalControl()
        
        # Validate inputs
        try:
            dns_type_raw = request.form.get('dns_type', '')
            primary_dns_raw = request.form.get('primary_dns', '').strip()
            secondary_dns_raw = request.form.get('secondary_dns', '').strip()
            
            # Validate DNS type
            dns_type = InputValidator.validate_dns_type(dns_type_raw)
            
            # Validate DNS servers if needed
            if dns_type == 'custom':
                if not primary_dns_raw:
                    flash("Primary DNS server is required for custom DNS", "danger")
                    return redirect(url_for('dns_settings'))
                
                primary_dns = InputValidator.validate_ip_address(primary_dns_raw)
                secondary_dns = None
                
                if secondary_dns_raw:
                    secondary_dns = InputValidator.validate_ip_address(secondary_dns_raw)
            else:
                # For predefined DNS types, use default values
                primary_dns = primary_dns_raw  # Will be set by the control logic
                secondary_dns = secondary_dns_raw or None
                
        except ValidationError as e:
            flash(f"Invalid input: {str(e)}", "danger")
            return redirect(url_for('dns_settings'))
            
        control.set_dns_settings(dns_type, primary_dns, secondary_dns)
        flash("DNS settings updated successfully!", "success")
        
    except Exception as e:
        logging.error(f"Error updating DNS settings: {str(e)}")
        flash(f"Failed to update DNS settings: {str(e)}", "danger")
    
    return redirect(url_for('dns_settings'))

@app.route('/blacklists', methods=['GET', 'POST'])
@login_required
def blacklists():
    """Display and manage content filtering settings"""
    pc = ParentalControl()
    
    # Get blocked sites and categories
    blocked_sites = pc.get_blocked_sites() if hasattr(pc, 'get_blocked_sites') else []
    blocked_categories = pc.get_blocked_categories() if hasattr(pc, 'get_blocked_categories') else []
    
    # Get real available categories from BlacklistManager
    try:
        available_categories = pc.blacklist_manager.get_available_categories()
        
        # Get actual domain counts and last updated info from database
        db_categories = pc.db.get_blacklist_categories(active_only=False)
        
        # Enhance available categories with database info
        for cat in available_categories:
            # Find matching database category
            db_cat = next((db_c for db_c in db_categories if db_c['name'] == cat['name']), None)
            if db_cat:
                cat['domain_count'] = db_cat.get('domain_count', 0)
                cat['last_updated'] = db_cat.get('last_updated', 'Never')
                cat['is_active'] = db_cat.get('is_active', False)
            else:
                cat['domain_count'] = 0
                cat['last_updated'] = 'Never'
                cat['is_active'] = False
                
    except Exception as e:
        logging.error(f"Error getting available categories: {e}")
        # Fallback to basic categories if there's an error
        available_categories = [
            {'name': 'adult', 'description': 'Adult content', 'domain_count': 0, 'last_updated': 'Never', 'is_active': False},
            {'name': 'gambling', 'description': 'Online gambling and betting sites', 'domain_count': 0, 'last_updated': 'Never', 'is_active': False},
            {'name': 'social_networks', 'description': 'Social media and networking sites', 'domain_count': 0, 'last_updated': 'Never', 'is_active': False},
            {'name': 'porn', 'description': 'Pornography', 'domain_count': 0, 'last_updated': 'Never', 'is_active': False},
        ]
    
    # Get active category names from database
    active_category_names = [cat['name'] for cat in available_categories if cat.get('is_active', False)]
    
    # Calculate statistics for template
    active_categories = [cat for cat in available_categories if cat['name'] in active_category_names]
    total_domains = len(blocked_sites) + sum(cat.get('domain_count', 0) for cat in active_categories)
    last_updated = max([cat.get('last_updated') for cat in available_categories], default=None) if available_categories else None
    
    if request.method == 'POST' and 'update_blacklists' in request.form:
        # Handle category updates
        selected_categories = request.form.getlist('categories')
        
        try:
            # Update blacklist categories
            if selected_categories:
                logging.info(f"Updating blacklist categories: {selected_categories}")
                
                # Use the blacklist manager to download and update categories
                results = {}
                total_domains = 0
                
                for category in selected_categories:
                    try:
                        success, num_domains = pc.update_blacklist(category)
                        if success:
                            results[category] = num_domains
                            total_domains += num_domains
                            logging.info(f"Updated {category}: {num_domains} domains")
                        else:
                            logging.error(f"Failed to update {category}")
                            flash(f"Failed to update {category} blacklist", "warning")
                    except Exception as e:
                        logging.error(f"Error updating {category}: {e}")
                        flash(f"Error updating {category}: {str(e)}", "warning")
                
                # Set active categories in database
                if results:
                    pc.db.set_blacklist_categories(selected_categories)
                    
                    # Update hosts file with all blocked domains
                    pc._update_hosts_file()
                    
                    flash(f'Successfully updated {len(results)} blacklist categories with {total_domains:,} total domains', 'success')
                else:
                    flash('No blacklist categories were successfully updated', 'warning')
            else:
                # No categories selected - disable all
                pc.db.set_blacklist_categories([])
                pc._update_hosts_file()  # Update hosts file to remove blacklist blocks
                flash('All blacklist categories disabled', 'info')
                
        except Exception as e:
            logging.error(f"Error updating blacklists: {e}")
            flash(f'Error updating blacklists: {str(e)}', 'danger')
        
        return redirect(url_for('blacklists'))
    
    return render_template('blacklists.html',
                         available_categories=available_categories,
                         active_category_names=active_category_names,
                         active_categories=active_categories,
                         blocked_sites=blocked_sites,
                         blocked_categories=blocked_categories,
                         total_domains=total_domains,
                         last_updated=last_updated,
                         current_page='blacklists')

@app.route('/time-management')
@login_required
def time_management():
    """Display time management settings"""
    try:
        pc = ParentalControl()
        
        # Get today's usage data
        today_usage = pc.time_manager.get_todays_usage()
        
        # Get daily limit data
        daily_limit = pc.time_manager.get_daily_limit()
        if not daily_limit:
            daily_limit = {
                'time_limit_minutes': 480,  # 8 hours default
                'is_active': False,
                'reset_time': '00:00'
            }
        
        # Get real schedules data
        schedules = pc.time_manager.get_schedules(active_only=False)
        
        # Usage limits (for display)
        usage_limits = {
            'daily_minutes': daily_limit.get('time_limit_minutes', 480),
            'weekly_minutes': daily_limit.get('time_limit_minutes', 480) * 7
        }
        
        # Calculate usage percentage
        daily_limit_minutes = daily_limit.get('time_limit_minutes', 480)
        usage_percent = min(100, (today_usage / daily_limit_minutes) * 100) if daily_limit_minutes > 0 else 0
        remaining_time = max(0, daily_limit_minutes - today_usage)

        # Get current access status (for time restriction enforcement)
        is_allowed, status_reason = pc.time_manager.is_access_allowed()

        return render_template('time_management.html',
                             current_page='time_management',
                             daily_limit=daily_limit,
                             today_usage=today_usage,
                             schedules=schedules,
                             usage_limits=usage_limits,
                             usage_percent=usage_percent,
                             remaining_time=remaining_time,
                             is_allowed=is_allowed,
                             status_reason=status_reason)
                             
    except Exception as e:
        logging.error(f"Error in time_management route: {str(e)}")
        # Provide minimal data to prevent template errors
        return render_template('time_management.html',
                             current_page='time_management',
                             daily_limit={'time_limit_minutes': 480, 'is_active': False},
                             today_usage=0,
                             schedules=[],
                             usage_limits={'daily_minutes': 480, 'weekly_minutes': 3360},
                             usage_percent=0,
                             remaining_time=480,
                             is_allowed=True,
                             status_reason='Error loading status')

@app.route('/reports')
@login_required
def reports():
    """Display activity reports"""
    # Placeholder data
    return render_template('reports.html', current_page='reports')

@app.route('/blacklist-domains/<category>')
@login_required
def blacklist_domains(category):
    """Display domains for a specific blacklist category"""
    try:
        pc = ParentalControl()
        
        # Get domains for the category
        domains = pc.db.get_blacklist_domains(category)
        
        # Get category info
        available_categories = pc.blacklist_manager.get_available_categories()
        category_info = next((cat for cat in available_categories if cat['name'] == category), None)
        
        if not category_info:
            flash(f'Category "{category}" not found', 'danger')
            return redirect(url_for('blacklists'))
        
        # Get database info for this category
        db_categories = pc.db.get_blacklist_categories(active_only=False)
        db_cat = next((db_c for db_c in db_categories if db_c['name'] == category), None)
        
        if db_cat:
            category_info.update({
                'domain_count': db_cat.get('domain_count', 0),
                'last_updated': db_cat.get('last_updated', 'Never'),
                'is_active': db_cat.get('is_active', False)
            })
        else:
            category_info.update({
                'domain_count': 0,
                'last_updated': 'Never',
                'is_active': False
            })
        
        # Paginate domains (show 100 per page)
        page = int(request.args.get('page', 1))
        per_page = 100
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        paginated_domains = domains[start_idx:end_idx]
        total_pages = (len(domains) + per_page - 1) // per_page
        
        return render_template('blacklist_domains.html',
                             category=category,
                             category_info=category_info,
                             domains=paginated_domains,
                             total_domains=len(domains),
                             current_page_num=page,
                             total_pages=total_pages,
                             current_page='blacklists')
        
    except Exception as e:
        logging.error(f"Error displaying domains for category {category}: {e}")
        flash(f'Error loading domains for category "{category}"', 'danger')
        return redirect(url_for('blacklists'))

@app.route('/add_blocked_site', methods=['POST'])
@login_required
def add_blocked_site():
    """Add a site to the blocked list"""
    try:
        domain_raw = request.form.get('domain', '')
        category_raw = request.form.get('category', 'MANUAL')
        
        # Validate and sanitize inputs
        try:
            domain = InputValidator.validate_domain(domain_raw)
            category = InputValidator.sanitize_string(category_raw, max_length=50)
        except ValidationError as e:
            flash(f'Invalid input: {str(e)}', 'danger')
            return redirect(url_for('index'))
        
        pc = ParentalControl()
        
        # Check if already blocked
        if pc.db.is_site_blocked(domain):
            flash(f'Domain "{domain}" is already blocked', 'warning')
            return redirect(url_for('index'))
        
        # Add to blocked sites
        success = pc.db.add_blocked_site(domain, category)
        
        if success:
            # Update hosts file
            pc._update_hosts_file()
            flash(f'Successfully blocked "{domain}"', 'success')
            logging.info(f"Manually blocked domain: {domain}")
        else:
            flash(f'Failed to block "{domain}"', 'danger')
            logging.error(f"Failed to block domain: {domain}")
            
    except Exception as e:
        logging.error(f"Error adding blocked site: {e}")
        flash(f'Error blocking site: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/remove_blocked_site', methods=['POST'])
@login_required
def remove_blocked_site():
    """Remove a manually blocked site"""
    try:
        domain = request.form.get('domain')
        if domain:
            pc = ParentalControl()
            success = pc.db.remove_blocked_site(domain)
            if success:
                # Update hosts file after removing site
                pc._update_hosts_file()
                flash(f'Successfully removed {domain} from blocked sites', 'success')
            else:
                flash(f'Failed to remove {domain}', 'error')
        else:
            flash('No domain specified', 'error')
    except Exception as e:
        logging.error(f"Error removing blocked site: {e}")
        flash(f'Error removing site: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/start_blocking_server', methods=['POST'])
@login_required
def start_blocking_server():
    """Start the blocking server for friendly block pages"""
    try:
        pc = ParentalControl()
        success = pc.start_blocking_server()
        if success:
            flash('Blocking server started successfully! Blocked sites will now show friendly pages.', 'success')
        else:
            flash('Failed to start blocking server', 'error')
    except Exception as e:
        flash(f'Error starting blocking server: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/stop_blocking_server', methods=['POST'])
@login_required
def stop_blocking_server():
    """Stop the blocking server"""
    try:
        pc = ParentalControl()
        pc.stop_blocking_server()
        flash('Blocking server stopped', 'info')
    except Exception as e:
        flash(f'Error stopping blocking server: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/add_schedule', methods=['POST'])
@login_required
def add_schedule():
    """Add a new time schedule"""
    try:
        pc = ParentalControl()

        # DEBUG: Log all form data
        logging.info(f"=== ADD SCHEDULE DEBUG ===")
        logging.info(f"Form data: {dict(request.form)}")
        logging.info(f"Form lists: {request.form.lists()}")

        name = request.form.get('name', '').strip()
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()
        days = request.form.getlist('days')  # List of selected days
        is_active = request.form.get('is_active') == 'on'

        logging.info(f"Parsed: name='{name}', start='{start_time}', end='{end_time}', days={days}, active={is_active}")

        if not name or not start_time or not end_time:
            flash('Schedule name, start time, and end time are required', 'danger')
            return redirect(url_for('time_management'))
        
        # Convert day names to numbers (0=Monday, 6=Sunday)
        day_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        day_numbers = [day_mapping[day.lower()] for day in days if day.lower() in day_mapping]
        
        if not day_numbers:
            flash('At least one day must be selected', 'danger')
            return redirect(url_for('time_management'))
        
        success = pc.time_manager.add_schedule(name, start_time, end_time, day_numbers, is_active)
        
        if success:
            flash(f'Schedule "{name}" added successfully', 'success')
        else:
            flash('Failed to add schedule', 'danger')
            
    except Exception as e:
        logging.error(f"Error adding schedule: {e}")
        flash(f'Error adding schedule: {str(e)}', 'danger')
    
    return redirect(url_for('time_management'))

@app.route('/update_daily_limit', methods=['POST'])
@login_required
def update_daily_limit():
    """Update daily usage limit"""
    try:
        pc = ParentalControl()
        
        limit_minutes = request.form.get('limit_minutes', type=int)
        reset_time = request.form.get('reset_time', '00:00').strip()
        
        if limit_minutes is None or limit_minutes < 0:
            flash('Please enter a valid daily limit in minutes', 'danger')
            return redirect(url_for('time_management'))
        
        success = pc.time_manager.set_daily_limit(limit_minutes, reset_time)
        
        if success:
            flash(f'Daily limit set to {limit_minutes} minutes', 'success')
        else:
            flash('Failed to update daily limit', 'danger')
            
    except Exception as e:
        logging.error(f"Error updating daily limit: {e}")
        flash(f'Error updating daily limit: {str(e)}', 'danger')
    
    return redirect(url_for('time_management'))

@app.route('/blocked')
def blocked():
    """Display blocked page for restricted content"""
    # Get parameters from URL
    blocked_url = request.args.get('url', 'Unknown URL')
    block_reason = request.args.get('reason', 'Content blocked by parental control')
    block_category = request.args.get('category', '')
    time_restriction = request.args.get('time_restriction', '')
    
    return render_template('blocked.html',
                         blocked_url=blocked_url,
                         block_reason=block_reason,
                         block_category=block_category,
                         time_restriction=time_restriction)

@app.route('/help')
@login_required
def help():
    """Display help and documentation"""
    return render_template('help.html', current_page='help')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allow admin to change password"""
    if request.method == 'POST':
        try:
            current_password = request.form.get('current_password', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not all([current_password, new_password, confirm_password]):
                flash('All fields are required', 'danger')
                return render_template('change_password.html')
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return render_template('change_password.html')
            
            if len(new_password) < 4:
                flash('New password must be at least 4 characters', 'danger')
                return render_template('change_password.html')
            
            control = ParentalControl()
            
            # Verify current password
            if not control.verify_password(current_password):
                flash('Current password is incorrect', 'danger')
                return render_template('change_password.html')
            
            # Set new password
            if control.set_password(new_password):
                flash('Password changed successfully', 'success')
                logging.info("Admin password changed")
                return redirect(url_for('index'))
            else:
                flash('Failed to change password', 'danger')
                
        except Exception as e:
            logging.error(f"Error changing password: {e}")
            flash(f'Error changing password: {str(e)}', 'danger')
    
    return render_template('change_password.html', current_page='settings')

# =============================================================================
# Category Management Routes
# =============================================================================

@app.route('/categories')
@login_required
def categories():
    """Display unified category management page."""
    return render_template('categories.html', current_page='categories')

# =============================================================================
# Category Management API Endpoints
# =============================================================================

@app.route('/api/categories', methods=['GET'])
@login_required
def api_get_categories():
    """Get all categories with their status."""
    try:
        from parental_control.category_manager import CategoryManager

        pc = ParentalControl()
        category_manager = CategoryManager(pc.db, pc.blacklist_manager)

        categories = category_manager.get_all_categories()

        return jsonify(categories), 200
    except Exception as e:
        logging.error(f"Error getting categories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<category_id>', methods=['GET'])
@login_required
def api_get_category(category_id):
    """Get a single category by ID."""
    try:
        from parental_control.category_manager import CategoryManager

        pc = ParentalControl()
        category_manager = CategoryManager(pc.db, pc.blacklist_manager)

        category = category_manager.get_category(category_id)

        if not category:
            return jsonify({'error': 'Category not found'}), 404

        return jsonify(category), 200
    except Exception as e:
        logging.error(f"Error getting category {category_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<category_id>/toggle', methods=['POST'])
@login_required
def api_toggle_category(category_id):
    """Toggle category blocking status."""
    try:
        from parental_control.category_manager import CategoryManager

        data = request.get_json()
        if not data or 'blocked' not in data:
            return jsonify({'error': 'Missing "blocked" parameter'}), 400

        blocked = data['blocked']

        pc = ParentalControl()
        category_manager = CategoryManager(pc.db, pc.blacklist_manager)

        success, message = category_manager.toggle_category_blocking(category_id, blocked)

        if success:
            # Update hosts file to apply changes
            pc._update_hosts_file()

            return jsonify({
                'success': True,
                'is_blocked': blocked,
                'message': message
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
    except Exception as e:
        logging.error(f"Error toggling category {category_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<category_id>/domains', methods=['GET'])
@login_required
def api_get_category_domains(category_id):
    """Get domains for a category with pagination and search."""
    try:
        from parental_control.category_manager import CategoryManager

        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        search = request.args.get('search', None, type=str)

        offset = (page - 1) * limit

        pc = ParentalControl()
        category_manager = CategoryManager(pc.db, pc.blacklist_manager)

        result = category_manager.get_category_domains(category_id, limit, offset, search)

        if 'error' in result:
            return jsonify(result), 404

        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error getting domains for category {category_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<category_id>/update', methods=['POST'])
@login_required
def api_update_category(category_id):
    """Download/update category domains from UT1."""
    try:
        from parental_control.category_manager import CategoryManager

        pc = ParentalControl()
        category_manager = CategoryManager(pc.db, pc.blacklist_manager)

        success, message, domain_count = category_manager.update_category(category_id)

        if success:
            # Update hosts file if category is blocked
            category = category_manager.get_category(category_id)
            if category and category['is_blocked']:
                pc._update_hosts_file()

            return jsonify({
                'success': True,
                'message': message,
                'domain_count': domain_count,
                'status': 'updated',
                'last_updated': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
    except Exception as e:
        logging.error(f"Error updating category {category_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/<category_id>/update-status', methods=['GET'])
@login_required
def api_get_category_update_status(category_id):
    """Get current update status for progress tracking."""
    try:
        from parental_control.category_manager import CategoryManager

        pc = ParentalControl()
        category_manager = CategoryManager(pc.db, pc.blacklist_manager)

        status = category_manager.get_category_update_status(category_id)

        return jsonify(status), 200
    except Exception as e:
        logging.error(f"Error getting update status for category {category_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/bulk-toggle', methods=['POST'])
@login_required
def api_bulk_toggle_categories():
    """Toggle multiple categories at once."""
    try:
        from parental_control.category_manager import CategoryManager

        data = request.get_json()
        if not data or 'category_ids' not in data or 'blocked' not in data:
            return jsonify({'error': 'Missing "category_ids" or "blocked" parameter'}), 400

        category_ids = data['category_ids']
        blocked = data['blocked']

        pc = ParentalControl()
        category_manager = CategoryManager(pc.db, pc.blacklist_manager)

        results = category_manager.bulk_toggle(category_ids, blocked)

        if results['success'] or results['updated_count'] > 0:
            # Update hosts file to apply changes
            pc._update_hosts_file()

        return jsonify(results), 200
    except Exception as e:
        logging.error(f"Error bulk toggling categories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories/bulk-update', methods=['POST'])
@login_required
def api_bulk_update_categories():
    """Update multiple UT1 categories at once."""
    try:
        from parental_control.category_manager import CategoryManager

        data = request.get_json()
        if not data or 'category_ids' not in data:
            return jsonify({'error': 'Missing "category_ids" parameter'}), 400

        category_ids = data['category_ids']

        pc = ParentalControl()
        category_manager = CategoryManager(pc.db, pc.blacklist_manager)

        results = category_manager.bulk_update(category_ids)

        if results['success'] or results['updated_count'] > 0:
            # Update hosts file for any blocked categories
            pc._update_hosts_file()

        return jsonify(results), 200
    except Exception as e:
        logging.error(f"Error bulk updating categories: {e}")
        return jsonify({'error': str(e)}), 500

def main():
    try:
        print("Checking if running as root...")  # Debug print
        if os.geteuid() != 0:
            print("This program requires root privileges.")
            sys.exit(1)
        
        # Ensure directories exist
        os.makedirs('/var/log/ubuntu-parental', exist_ok=True)
        
        print("Starting Flask app...")  # Debug print
        logging.info("Starting Flask application")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error starting app: {str(e)}")  # Debug print
        logging.error(f"Startup error: {str(e)}")
        raise

if __name__ == '__main__':
    print("Entering main...")  # Debug print
    main()