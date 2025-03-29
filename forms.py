from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, IPAddress, Optional, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')

class NetworkInterfaceForm(FlaskForm):
    name = StringField('Interface Name', validators=[DataRequired()])
    type = SelectField('Type', choices=[
        ('ethernet', 'Ethernet'),
        ('wifi', 'WiFi'),
        ('cellular', 'Cellular')
    ])
    dhcp_enabled = BooleanField('Enable DHCP')
    ip_address = StringField('IP Address', validators=[Optional(), IPAddress()])
    netmask = StringField('Netmask', validators=[Optional()])
    gateway = StringField('Gateway', validators=[Optional(), IPAddress()])
    dns_servers = StringField('DNS Servers (comma separated)')
    is_wan = BooleanField('WAN Interface')
    enabled = BooleanField('Enabled')
    submit = SubmitField('Save')

class FreeswitchConfigForm(FlaskForm):
    enabled = BooleanField('Enable FreeSWITCH')
    sip_port = IntegerField('SIP Port', validators=[NumberRange(min=1024, max=65535)])
    rtp_port_min = IntegerField('RTP Port Min', validators=[NumberRange(min=1024, max=65535)])
    rtp_port_max = IntegerField('RTP Port Max', validators=[NumberRange(min=1024, max=65535)])
    external_ip = StringField('External IP', validators=[Optional(), IPAddress()])
    log_level = SelectField('Log Level', choices=[
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('notice', 'Notice'),
        ('warning', 'Warning'),
        ('err', 'Error'),
        ('crit', 'Critical')
    ])
    submit = SubmitField('Save')

class FreeswitchExtensionForm(FlaskForm):
    extension = StringField('Extension Number', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    voicemail_enabled = BooleanField('Enable Voicemail')
    voicemail_pin = StringField('Voicemail PIN', validators=[Optional(), Length(min=4)])
    submit = SubmitField('Save')

class DiagnosticsForm(FlaskForm):
    ping_target = StringField('Ping Target', validators=[DataRequired()])
    ping_submit = SubmitField('Ping')
    
    traceroute_target = StringField('Traceroute Target', validators=[DataRequired()])
    traceroute_submit = SubmitField('Traceroute')
    
    dns_target = StringField('DNS Lookup', validators=[DataRequired()])
    dns_submit = SubmitField('Lookup')

class ApiClientForm(FlaskForm):
    name = StringField('Client Name', validators=[DataRequired()])
    ip_whitelist = StringField('IP Whitelist (comma separated)')
    enabled = BooleanField('Enabled')
    submit = SubmitField('Save')

class WizardNetworkForm(FlaskForm):
    internet_type = SelectField('Internet Connection Type', choices=[
        ('dhcp', 'Automatic (DHCP)'),
        ('static', 'Static IP'),
        ('pppoe', 'PPPoE (DSL)')
    ])
    
    # Static IP fields
    static_ip = StringField('IP Address', validators=[Optional(), IPAddress()])
    static_netmask = StringField('Subnet Mask', validators=[Optional()])
    static_gateway = StringField('Gateway', validators=[Optional(), IPAddress()])
    static_dns1 = StringField('Primary DNS', validators=[Optional(), IPAddress()])
    static_dns2 = StringField('Secondary DNS', validators=[Optional(), IPAddress()])
    
    # PPPoE fields
    pppoe_username = StringField('PPPoE Username')
    pppoe_password = PasswordField('PPPoE Password')
    
    # WiFi AP Settings
    wifi_enabled = BooleanField('Enable WiFi')
    wifi_ssid = StringField('WiFi Network Name (SSID)')
    wifi_password = PasswordField('WiFi Password', validators=[Optional(), Length(min=8)])
    
    submit = SubmitField('Next')

class WizardFreeswitchForm(FlaskForm):
    enable_freeswitch = BooleanField('Enable FreeSWITCH PBX')
    
    # Basic PBX settings
    company_name = StringField('Company Name')
    
    # Extensions
    num_extensions = IntegerField('Number of Extensions', default=2, validators=[NumberRange(min=0, max=20)])
    extension_prefix = StringField('Extension Prefix', default='10')
    
    # Trunk settings
    trunk_enabled = BooleanField('Enable SIP Trunk')
    trunk_provider = StringField('Trunk Provider')
    trunk_username = StringField('Trunk Username')
    trunk_password = PasswordField('Trunk Password')
    trunk_server = StringField('Trunk Server')
    
    submit = SubmitField('Finish')
