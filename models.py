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
    caller_id_name = db.Column(db.String(64))  # Nome da mostrare per chiamate in uscita
    caller_id_number = db.Column(db.String(32))  # Numero da mostrare per chiamate in uscita
    
    # Voicemail settings
    voicemail_enabled = db.Column(db.Boolean, default=True)
    voicemail_pin = db.Column(db.String(16))
    voicemail_email = db.Column(db.String(128))  # Email per invio voicemail
    voicemail_attach_file = db.Column(db.Boolean, default=True)  # Invia voicemail come allegato email
    voicemail_delete_after_email = db.Column(db.Boolean, default=False)  # Cancella dopo invio email
    
    # Call recording settings
    record_inbound = db.Column(db.Boolean, default=False)  # Registra chiamate in entrata
    record_outbound = db.Column(db.Boolean, default=False)  # Registra chiamate in uscita
    
    # Hot desking
    hot_desk_enabled = db.Column(db.Boolean, default=False)  # Supporto hot desking
    hot_desk_pin = db.Column(db.String(16))  # PIN per hot desking
    hot_desk_logged_in = db.Column(db.Boolean, default=False)  # Stato login hot desking
    hot_desk_device = db.Column(db.String(64))  # Device dove è loggato
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    voicemail_messages = db.relationship('VoicemailMessage', backref='mailbox', lazy=True, cascade="all, delete-orphan")
    
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

# Modelli per le nuove funzionalità del centralino

class IvrMenu(db.Model):
    """Interactive Voice Response menu"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255))
    greeting_message = db.Column(db.String(512), nullable=False)
    timeout = db.Column(db.Integer, default=10)  # Timeout in secondi
    max_failures = db.Column(db.Integer, default=3)  # Numero massimo di tentativi falliti
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    options = db.relationship('IvrOption', backref='menu', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<IvrMenu {self.name}>'

class IvrOption(db.Model):
    """Option for IVR menu"""
    id = db.Column(db.Integer, primary_key=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('ivr_menu.id'), nullable=False)
    digit = db.Column(db.String(1), nullable=False)  # Tasto da premere (0-9, *, #)
    action_type = db.Column(db.String(32), nullable=False)  # extension, voicemail, queue, submenu, etc.
    action_data = db.Column(db.String(128), nullable=False)  # Extension number, queue name, submenu id, etc.
    description = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<IvrOption {self.menu_id}:{self.digit} -> {self.action_type}>'

class CallQueue(db.Model):
    """Call queues for call center functionality"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    strategy = db.Column(db.String(32), default='round-robin')  # round-robin, least-recent, random, etc.
    moh_class = db.Column(db.String(64), default='default')  # Music on hold class
    announce_position = db.Column(db.Boolean, default=False)  # Announce position in queue
    announce_holdtime = db.Column(db.Boolean, default=False)  # Announce estimated hold time
    max_wait_time = db.Column(db.Integer, default=300)  # Max wait time in seconds
    max_callers = db.Column(db.Integer, default=10)  # Max number of callers in queue
    timeout = db.Column(db.Integer, default=60)  # Agent ring timeout in seconds
    wrapup_time = db.Column(db.Integer, default=5)  # Agent wrapup time in seconds
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    members = db.relationship('QueueMember', backref='queue', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CallQueue {self.name}>'

class QueueMember(db.Model):
    """Agenti assegnati a una coda"""
    id = db.Column(db.Integer, primary_key=True)
    queue_id = db.Column(db.Integer, db.ForeignKey('call_queue.id'), nullable=False)
    extension_id = db.Column(db.Integer, db.ForeignKey('sip_extension.id'), nullable=False)
    priority = db.Column(db.Integer, default=1)  # Priority (1-10, lower is higher priority)
    penalty = db.Column(db.Integer, default=0)  # Penalty (0-10, higher is less likely to get calls)
    
    # Relazione alla extension
    extension = db.relationship('SipExtension')
    
    def __repr__(self):
        return f'<QueueMember {self.queue_id}:{self.extension_id}>'

class TimeCondition(db.Model):
    """Time-based routing conditions"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    days_of_week = db.Column(db.String(32), default='1,2,3,4,5')  # 0=Sun, 1=Mon, etc.
    time_start = db.Column(db.Time, nullable=False)
    time_end = db.Column(db.Time, nullable=False)
    destination_match = db.Column(db.String(32), nullable=False)  # extension, ivr, queue, etc.
    destination_match_id = db.Column(db.Integer, nullable=False)  # ID of the destination
    fallback_destination = db.Column(db.String(32))  # extension, ivr, queue, etc.
    fallback_destination_id = db.Column(db.Integer)  # ID of the fallback
    enabled = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<TimeCondition {self.name}>'

class InboundRoute(db.Model):
    """Inbound call routing configuration"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    did_number = db.Column(db.String(32), nullable=False)  # DID/DDI number to match
    trunk_id = db.Column(db.Integer, db.ForeignKey('sip_trunk.id'))
    destination_type = db.Column(db.String(32), nullable=False)  # extension, ivr, queue, etc.
    destination_id = db.Column(db.Integer, nullable=False)  # ID of the destination
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazione opzionale al trunk
    trunk = db.relationship('SipTrunk')
    
    def __repr__(self):
        return f'<InboundRoute {self.name} ({self.did_number})>'

class OutboundRoute(db.Model):
    """Outbound call routing configuration"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    pattern = db.Column(db.String(64), nullable=False)  # Pattern to match (e.g. _39X. for Italy)
    trunk_id = db.Column(db.Integer, db.ForeignKey('sip_trunk.id'), nullable=False)
    priority = db.Column(db.Integer, default=1)  # Lower number = higher priority
    prefix = db.Column(db.String(16))  # Prefix to add
    strip = db.Column(db.Integer, default=0)  # Number of digits to strip from the beginning
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazione al trunk
    trunk = db.relationship('SipTrunk')
    
    def __repr__(self):
        return f'<OutboundRoute {self.name} ({self.pattern}) -> Trunk {self.trunk_id}>'

class CallRecording(db.Model):
    """Call recording settings and records"""
    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.String(64), unique=True, nullable=False)  # Call UUID
    caller = db.Column(db.String(64), nullable=False)
    callee = db.Column(db.String(64), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # Duration in seconds
    recording_path = db.Column(db.String(256))
    recording_size = db.Column(db.Integer)  # Size in bytes
    call_direction = db.Column(db.String(16))  # inbound, outbound, internal
    trunk_id = db.Column(db.Integer, db.ForeignKey('sip_trunk.id'))  # For inbound/outbound
    
    # Relazione opzionale al trunk
    trunk = db.relationship('SipTrunk')
    
    def __repr__(self):
        return f'<CallRecording {self.call_id}>'

class Blacklist(db.Model):
    """Blacklisted caller numbers"""
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(32), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Blacklist {self.number}>'

class VoicemailMessage(db.Model):
    """Voicemail messages"""
    id = db.Column(db.Integer, primary_key=True)
    extension_id = db.Column(db.Integer, db.ForeignKey('sip_extension.id'), nullable=False)
    caller = db.Column(db.String(64))
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Integer)  # Duration in seconds
    message_path = db.Column(db.String(256))
    listened = db.Column(db.Boolean, default=False)
    forwarded_to_email = db.Column(db.Boolean, default=False)
    
    # Relazione alla extension
    extension = db.relationship('SipExtension')
    
    def __repr__(self):
        return f'<VoicemailMessage {self.id} for {self.extension_id}>'


class VpnServer(db.Model):
    """VPN Server Configuration"""
    id = db.Column(db.Integer, primary_key=True)
    enabled = db.Column(db.Boolean, default=False)
    vpn_type = db.Column(db.String(16), default='openvpn')  # openvpn, wireguard
    protocol = db.Column(db.String(8), default='udp')  # udp, tcp
    port = db.Column(db.Integer, default=1194)
    subnet = db.Column(db.String(18), default='10.8.0.0/24')
    dns_servers = db.Column(db.String(128))
    server_certificates_path = db.Column(db.String(255))
    cipher = db.Column(db.String(32), default='AES-256-GCM')
    auth_method = db.Column(db.String(16), default='certificate')  # certificate, password, both
    status = db.Column(db.String(16), default='stopped')  # running, stopped, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazione con i client VPN
    clients = db.relationship('VpnClient', backref='server', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<VpnServer {self.vpn_type}:{self.port}>'


class VpnClient(db.Model):
    """VPN Client Configuration"""
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('vpn_server.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255))
    client_id = db.Column(db.String(64), unique=True)
    ip_address = db.Column(db.String(15))  # Static IP if assigned
    certificates_path = db.Column(db.String(255))
    config_file_path = db.Column(db.String(255))
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_connected = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<VpnClient {self.name}>'
