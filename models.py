from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def __repr__(self):
        return f'<User {self.username}>'

class NetworkConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    interface_name = db.Column(db.String(32), nullable=False)
    interface_type = db.Column(db.String(16), nullable=False)  # wan, lan, wifi
    ip_mode = db.Column(db.String(8), default='dhcp')  # dhcp, static
    ip_address = db.Column(db.String(15))
    subnet_mask = db.Column(db.String(15))
    gateway = db.Column(db.String(15))
    dns_servers = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<NetworkConfig {self.interface_name}>'

class FreeswitchConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, default=False)
    sip_port = db.Column(db.Integer, default=5060)
    rtp_port_start = db.Column(db.Integer, default=16384)
    rtp_port_end = db.Column(db.Integer, default=32768)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FreeswitchConfig {self.id}>'

class SipExtension(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extension_number = db.Column(db.String(16), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    voicemail_enabled = db.Column(db.Boolean, default=True)
    voicemail_pin = db.Column(db.String(16))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SipExtension {self.extension_number}>'

class SipTrunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    host = db.Column(db.String(128), nullable=False)
    port = db.Column(db.Integer, default=5060)
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SipTrunk {self.name}>'

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_type = db.Column(db.String(16), nullable=False)  # system, network, freeswitch, security
    level = db.Column(db.String(8), nullable=False)  # info, warning, error, debug
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SystemLog {self.id} {self.log_type}>'

class ApiToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    token_hash = db.Column(db.String(256), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    created_by = db.relationship('User', backref='api_tokens')

    def __repr__(self):
        return f'<ApiToken {self.name}>'
