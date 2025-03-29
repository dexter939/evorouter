from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    api_token = db.Column(db.String(256), nullable=True)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NetworkInterface(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    type = db.Column(db.String(32), nullable=False)  # ethernet, wifi, cellular, etc.
    mac_address = db.Column(db.String(32))
    ip_address = db.Column(db.String(32))
    netmask = db.Column(db.String(32))
    gateway = db.Column(db.String(32))
    dns_servers = db.Column(db.String(128))
    dhcp_enabled = db.Column(db.Boolean, default=True)
    is_wan = db.Column(db.Boolean, default=False)
    enabled = db.Column(db.Boolean, default=True)
    
class FreeswitchConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, default=False)
    sip_port = db.Column(db.Integer, default=5060)
    rtp_port_min = db.Column(db.Integer, default=10000)
    rtp_port_max = db.Column(db.Integer, default=20000)
    external_ip = db.Column(db.String(64))
    log_level = db.Column(db.String(32), default="info")
    
class FreeswitchExtension(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extension = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(64))
    password = db.Column(db.String(128), nullable=False)
    voicemail_enabled = db.Column(db.Boolean, default=False)
    voicemail_pin = db.Column(db.String(32))
    
class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(16), nullable=False)
    source = db.Column(db.String(64), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
class ApiClient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    api_key = db.Column(db.String(256), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    ip_whitelist = db.Column(db.String(256))  # Comma-separated IPs or CIDR
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
