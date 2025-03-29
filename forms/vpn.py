from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Length, ValidationError, IPAddress
import re

class VpnServerForm(FlaskForm):
    """Form per la configurazione del server VPN"""
    enabled = BooleanField('Abilitato')
    
    vpn_type = SelectField('Tipo VPN', 
                         choices=[('openvpn', 'OpenVPN'), ('wireguard', 'WireGuard')],
                         validators=[DataRequired()])
    
    port = IntegerField('Porta', 
                      validators=[DataRequired(), NumberRange(min=1024, max=65535, 
                                                           message='La porta deve essere compresa tra 1024 e 65535')],
                      default=1194)
    
    protocol = SelectField('Protocollo', 
                         choices=[('udp', 'UDP'), ('tcp', 'TCP')],
                         validators=[DataRequired()],
                         default='udp')
    
    subnet = StringField('Subnet', 
                       validators=[DataRequired()],
                       default='10.8.0.0/24')
    
    dns_servers = StringField('Server DNS', 
                            validators=[Optional()],
                            default='8.8.8.8,8.8.4.4')
    
    cipher = SelectField('Cifratura', 
                       choices=[
                           ('AES-256-GCM', 'AES-256-GCM'), 
                           ('AES-128-GCM', 'AES-128-GCM'),
                           ('CHACHA20-POLY1305', 'CHACHA20-POLY1305')
                       ],
                       validators=[DataRequired()],
                       default='AES-256-GCM')
    
    auth_method = SelectField('Metodo Autenticazione', 
                            choices=[
                                ('certificate', 'Certificato'), 
                                ('password', 'Password'),
                                ('both', 'Certificato + Password')
                            ],
                            validators=[DataRequired()],
                            default='certificate')
    
    submit = SubmitField('Salva Configurazione')
    
    def validate_subnet(self, subnet):
        """Validazione della subnet"""
        # Validazione base con regex
        subnet_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
        if not re.match(subnet_pattern, subnet.data):
            raise ValidationError('Formato subnet non valido. Usare il formato: xxx.xxx.xxx.xxx/xx')
        
        # Separare indirizzo IP e mask
        ip_part, mask_part = subnet.data.split('/')
        try:
            # Controllo che la mask sia valida
            mask = int(mask_part)
            if mask < 8 or mask > 30:
                raise ValidationError('La subnet mask deve essere compresa tra 8 e 30')
            
            # Controllo che l'IP sia valido
            octets = ip_part.split('.')
            if len(octets) != 4:
                raise ValidationError('L\'indirizzo IP deve avere 4 ottetti')
            
            for octet in octets:
                octet_int = int(octet)
                if octet_int < 0 or octet_int > 255:
                    raise ValidationError('Ogni ottetto dell\'indirizzo IP deve essere compreso tra 0 e 255')
                    
        except ValueError:
            raise ValidationError('Formato subnet non valido')
    
    def validate_dns_servers(self, dns_servers):
        """Validazione dei server DNS"""
        if not dns_servers.data:
            return
            
        dns_list = dns_servers.data.split(',')
        for dns in dns_list:
            dns = dns.strip()
            # Controllo formato IP
            octets = dns.split('.')
            if len(octets) != 4:
                raise ValidationError('Il server DNS deve essere un indirizzo IP valido')
            
            try:
                for octet in octets:
                    octet_int = int(octet)
                    if octet_int < 0 or octet_int > 255:
                        raise ValidationError('Ogni ottetto dell\'indirizzo IP deve essere compreso tra 0 e 255')
            except ValueError:
                raise ValidationError('Il server DNS deve essere un indirizzo IP valido')


class VpnWizardForm(FlaskForm):
    """Form per il wizard di configurazione VPN"""
    server_enabled = BooleanField('Abilita server VPN', default=True)
    
    # Server Type sarà gestito come campo radio/card nel frontend, non serve qui
    
    server_port = IntegerField('Porta Server', 
                            validators=[DataRequired(), NumberRange(min=1024, max=65535)],
                            default=1194)
    
    server_protocol = SelectField('Protocollo', 
                                choices=[('udp', 'UDP'), ('tcp', 'TCP')],
                                validators=[DataRequired()],
                                default='udp')
    
    server_subnet = StringField('Subnet VPN', 
                              validators=[DataRequired()],
                              default='10.8.0.0/24')
    
    client_count = IntegerField('Numero di Client', 
                              validators=[DataRequired(), NumberRange(min=1, max=10)],
                              default=1)


class VpnClientForm(FlaskForm):
    """Form per la gestione dei client VPN"""
    name = StringField('Nome Client', 
                     validators=[DataRequired(), Length(min=3, max=64)],
                     render_kw={"placeholder": "Client1"})
    
    description = TextAreaField('Descrizione', 
                              validators=[Optional(), Length(max=255)],
                              render_kw={"placeholder": "Dispositivo, utente o scopo di questo client"})
    
    ip_address = StringField('Indirizzo IP', 
                           validators=[Optional(), IPAddress(message='Inserire un indirizzo IP valido')],
                           render_kw={"placeholder": "10.8.0.2"})
    
    enabled = BooleanField('Abilitato', default=True)
    
    submit = SubmitField('Salva Client')