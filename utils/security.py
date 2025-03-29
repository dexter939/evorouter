import logging
import os
import secrets
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import PASSWORD_MIN_LENGTH, FAILED_LOGIN_ATTEMPTS, ACCOUNT_LOCKOUT_TIME
import socket
import ipaddress

# Create logger
logger = logging.getLogger(__name__)

def generate_secure_token(length=32):
    """
    Generate a secure random token
    
    Args:
        length: Length of token in bytes
        
    Returns:
        str: Secure random token
    """
    return secrets.token_urlsafe(length)

def hash_password(password):
    """
    Hash a password using Werkzeug's password hash function
    
    Args:
        password: Plain-text password
        
    Returns:
        str: Hashed password
    """
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """
    Verify a password against its hash
    
    Args:
        password_hash: Hashed password
        password: Plain-text password to verify
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return check_password_hash(password_hash, password)

def validate_password_strength(password):
    """
    Validate password strength
    
    Args:
        password: Plain-text password
        
    Returns:
        tuple: (bool, str) - (valid, error message)
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"La password deve essere lunga almeno {PASSWORD_MIN_LENGTH} caratteri"
    
    if not any(c.isupper() for c in password):
        return False, "La password deve contenere almeno una lettera maiuscola"
    
    if not any(c.islower() for c in password):
        return False, "La password deve contenere almeno una lettera minuscola"
    
    if not any(c.isdigit() for c in password):
        return False, "La password deve contenere almeno un numero"
    
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for c in password):
        return False, "La password deve contenere almeno un carattere speciale"
    
    return True, ""

def is_safe_ip(ip_address):
    """
    Check if an IP address is safe (not private or loopback)
    
    Args:
        ip_address: IP address to check
        
    Returns:
        bool: True if safe, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_address)
        return not (ip.is_private or ip.is_loopback or ip.is_link_local)
    except ValueError:
        return False

def is_safe_hostname(hostname):
    """
    Check if a hostname is safe
    
    Args:
        hostname: Hostname to check
        
    Returns:
        bool: True if safe, False otherwise
    """
    try:
        if not hostname:
            return False
            
        # Try to resolve the hostname
        ip = socket.gethostbyname(hostname)
        
        # Check if the resolved IP is safe
        return is_safe_ip(ip)
    except socket.gaierror:
        return False

def generate_jwt_token(user_id, expiry_minutes=60):
    """
    Generate a JWT token for API authentication
    
    Args:
        user_id: User ID to include in the token
        expiry_minutes: Token expiry time in minutes
        
    Returns:
        str: JWT token
    """
    try:
        # Get JWT secret key from environment or use a secure default
        secret_key = os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex())
        
        # Set token expiration time
        exp_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiry_minutes)
        
        # Create token payload
        payload = {
            'user_id': user_id,
            'exp': exp_time,
            'iat': datetime.datetime.utcnow(),
            'jti': secrets.token_hex(16)  # JWT ID for uniqueness
        }
        
        # Generate token
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        
        return token
    except Exception as e:
        logger.error(f"Error generating JWT token: {str(e)}")
        return None

def verify_jwt_token(token):
    """
    Verify a JWT token
    
    Args:
        token: JWT token to verify
        
    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        # Get JWT secret key from environment or use a secure default
        secret_key = os.environ.get('JWT_SECRET_KEY', os.urandom(32).hex())
        
        # Decode and verify token
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error verifying JWT token: {str(e)}")
        return None

def sanitize_input(input_string):
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        input_string: String to sanitize
        
    Returns:
        str: Sanitized string
    """
    if not input_string:
        return ""
    
    # Replace potentially dangerous characters
    sanitized = input_string.replace('<', '&lt;').replace('>', '&gt;')
    
    return sanitized
