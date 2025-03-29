import secrets
import string
import re
import ipaddress
import logging
from flask import request
from models import ApiClient

logger = logging.getLogger(__name__)

def generate_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in string.punctuation for c in password)):
            break
    return password

def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_hex(32)

def validate_api_key(request):
    """Validate API key from request headers and check IP whitelist"""
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        logger.warning("API request missing API key")
        return False
    
    client = ApiClient.query.filter_by(api_key=api_key, enabled=True).first()
    if not client:
        logger.warning(f"Invalid or disabled API key: {api_key[:8]}...")
        return False
    
    # Check IP whitelist if configured
    if client.ip_whitelist:
        client_ip = request.remote_addr
        if not is_ip_in_whitelist(client_ip, client.ip_whitelist):
            logger.warning(f"IP {client_ip} not in whitelist for API client {client.name}")
            return False
    
    return True

def is_ip_in_whitelist(ip, whitelist):
    """Check if an IP is in a whitelist of IPs or CIDR ranges"""
    if not whitelist:
        return True
    
    whitelist_entries = [entry.strip() for entry in whitelist.split(',')]
    
    for entry in whitelist_entries:
        if '/' in entry:  # CIDR notation
            try:
                network = ipaddress.ip_network(entry)
                if ipaddress.ip_address(ip) in network:
                    return True
            except ValueError:
                # Invalid CIDR, ignore
                pass
        else:  # Single IP
            if ip == entry:
                return True
    
    return False

def sanitize_input(input_string):
    """Sanitize user input to prevent command injection"""
    # Remove any potentially dangerous characters or patterns
    return re.sub(r'[;&|<>$]', '', input_string)
