from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, IPAddress, NumberRange, ValidationError
import ipaddress

class NetworkInterfaceForm(FlaskForm):
    """Form for configuring network interfaces"""
    ip_mode = SelectField('Modalità IP', choices=[
        ('dhcp', 'DHCP (automatico)'),
        ('static', 'IP Statico')
    ], validators=[DataRequired()])
    
    ip_address = StringField('Indirizzo IP', validators=[
        Optional(),
        IPAddress(message='Inserisci un indirizzo IP valido')
    ])
    
    subnet_mask = StringField('Subnet Mask', validators=[Optional()])
    
    gateway = StringField('Gateway', validators=[
        Optional(),
        IPAddress(message='Inserisci un indirizzo IP valido per il gateway')
    ])
    
    dns_servers = StringField('Server DNS', validators=[Optional()])
    
    submit = SubmitField('Salva Configurazione')
    
    def validate_subnet_mask(self, field):
        """Validate subnet mask format"""
        if self.ip_mode.data == 'static' and field.data:
            try:
                # Try to convert subnet mask to CIDR notation to validate it
                ipaddress.IPv4Network(f'0.0.0.0/{field.data}', False)
            except ValueError:
                raise ValidationError('Subnet mask non valida')

class DhcpServerForm(FlaskForm):
    """Form for configuring DHCP server"""
    enabled = BooleanField('Abilitato', default=True)
    
    start_ip = StringField('Inizio Range DHCP', validators=[
        Optional(),
        IPAddress(message='Inserisci un indirizzo IP valido')
    ])
    
    end_ip = StringField('Fine Range DHCP', validators=[
        Optional(),
        IPAddress(message='Inserisci un indirizzo IP valido')
    ])
    
    lease_time = IntegerField('Tempo di Lease (ore)', validators=[
        Optional(),
        NumberRange(min=1, max=168, message='Il tempo di lease deve essere tra 1 e 168 ore')
    ], default=24)
    
    submit = SubmitField('Salva Configurazione')
    
    def validate(self):
        """Custom validation to ensure DHCP range makes sense"""
        if not super().validate():
            return False
            
        if not self.enabled.data:
            return True
            
        # If DHCP is enabled, start and end IP are required
        if not self.start_ip.data:
            self.start_ip.errors = ['L\'indirizzo IP iniziale è obbligatorio']
            return False
            
        if not self.end_ip.data:
            self.end_ip.errors = ['L\'indirizzo IP finale è obbligatorio']
            return False
            
        # Check that start IP is before end IP
        try:
            start = ipaddress.IPv4Address(self.start_ip.data)
            end = ipaddress.IPv4Address(self.end_ip.data)
            
            if start >= end:
                self.end_ip.errors = ['L\'indirizzo IP finale deve essere maggiore dell\'indirizzo iniziale']
                return False
        except:
            # This should not happen as we already validated IP formats above
            pass
            
        return True

class DnsSettingsForm(FlaskForm):
    """Form for configuring DNS settings"""
    primary_dns = StringField('DNS Primario', validators=[
        DataRequired(message='Il DNS primario è obbligatorio'),
        IPAddress(message='Inserisci un indirizzo IP valido')
    ])
    
    secondary_dns = StringField('DNS Secondario', validators=[
        Optional(),
        IPAddress(message='Inserisci un indirizzo IP valido')
    ])
    
    submit = SubmitField('Salva Configurazione')
