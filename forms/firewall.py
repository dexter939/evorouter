"""
Forms per la gestione del firewall.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError, Regexp
import ipaddress

def validate_ip_or_network(form, field):
    """Validatore per indirizzi IP o reti"""
    if field.data and field.data.lower() != 'any':
        try:
            # Tenta di validare come indirizzo IP
            ipaddress.ip_address(field.data)
        except ValueError:
            try:
                # Tenta di validare come rete IP
                ipaddress.ip_network(field.data, strict=False)
            except ValueError:
                raise ValidationError('Inserire un indirizzo IP o una rete valida (es. 192.168.1.1 o 192.168.1.0/24)')

def validate_port_or_range(form, field):
    """Validatore per porte singole o intervalli"""
    if field.data and field.data.lower() != 'any':
        # Verifica se è un intervallo (formato start-end)
        if '-' in field.data:
            try:
                start, end = field.data.split('-')
                start_port = int(start.strip())
                end_port = int(end.strip())
                if start_port < 1 or start_port > 65535 or end_port < 1 or end_port > 65535:
                    raise ValidationError('Le porte devono essere comprese tra 1 e 65535')
                if start_port > end_port:
                    raise ValidationError('La porta iniziale deve essere minore della porta finale')
            except ValueError:
                raise ValidationError('Intervallo di porte non valido (es. 1000-2000)')
        # Verifica se è un elenco di porte separate da virgola
        elif ',' in field.data:
            try:
                ports = [int(p.strip()) for p in field.data.split(',')]
                for port in ports:
                    if port < 1 or port > 65535:
                        raise ValidationError('Le porte devono essere comprese tra 1 e 65535')
            except ValueError:
                raise ValidationError('Elenco di porte non valido (es. 80,443,8080)')
        # Altrimenti verifica se è una singola porta
        else:
            try:
                port = int(field.data)
                if port < 1 or port > 65535:
                    raise ValidationError('La porta deve essere compresa tra 1 e 65535')
            except ValueError:
                raise ValidationError('Porta non valida')

class FirewallZoneForm(FlaskForm):
    """Form per la creazione/modifica di una zona di firewall"""
    name = StringField('Nome', validators=[
        DataRequired(), 
        Length(min=2, max=32),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Il nome può contenere solo lettere, numeri e underscore')
    ])
    description = TextAreaField('Descrizione', validators=[Optional(), Length(max=255)])
    interfaces = StringField('Interfacce', validators=[DataRequired()])
    default_policy = SelectField('Policy Predefinita', choices=[
        ('accept', 'Accept - Accetta tutto il traffico'),
        ('drop', 'Drop - Scarta silenziosamente il traffico'),
        ('reject', 'Reject - Rifiuta il traffico con notifica')
    ], default='drop')
    masquerade = BooleanField('Abilita NAT Masquerading', default=False)
    mss_clamping = BooleanField('Abilita MSS Clamping per VPN', default=False)
    priority = IntegerField('Priorità', validators=[NumberRange(min=0, max=999)], default=0)
    submit = SubmitField('Salva Zona')

class FirewallRuleForm(FlaskForm):
    """Form per la creazione/modifica di una regola di firewall"""
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Descrizione', validators=[Optional(), Length(max=255)])
    zone_id = SelectField('Zona', coerce=int, validators=[DataRequired()])
    source = StringField('Origine', validators=[Optional(), validate_ip_or_network], default='any')
    destination = StringField('Destinazione', validators=[Optional(), validate_ip_or_network], default='any')
    protocol = SelectField('Protocollo', choices=[
        ('all', 'Tutti i protocolli'),
        ('tcp', 'TCP'),
        ('udp', 'UDP'),
        ('icmp', 'ICMP'),
        ('tcp,udp', 'TCP+UDP')
    ], default='all')
    src_port = StringField('Porta Origine', validators=[Optional(), validate_port_or_range], default='any')
    dst_port = StringField('Porta Destinazione', validators=[Optional(), validate_port_or_range], default='any')
    action = SelectField('Azione', choices=[
        ('accept', 'Accept - Accetta'),
        ('drop', 'Drop - Scarta'),
        ('reject', 'Reject - Rifiuta')
    ], default='drop')
    log = BooleanField('Registra nei log', default=False)
    enabled = BooleanField('Abilitata', default=True)
    priority = IntegerField('Priorità', validators=[NumberRange(min=0, max=999)], default=0)
    submit = SubmitField('Salva Regola')

class FirewallPortForwardingForm(FlaskForm):
    """Form per la creazione/modifica di un port forwarding"""
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Descrizione', validators=[Optional(), Length(max=255)])
    source_zone = SelectField('Zona di Origine', default='wan')
    dest_zone = SelectField('Zona di Destinazione', default='lan')
    protocol = SelectField('Protocollo', choices=[
        ('tcp', 'TCP'),
        ('udp', 'UDP'),
        ('tcp,udp', 'TCP+UDP')
    ], default='tcp')
    src_dip = StringField('IP di Destinazione Esterno (opzionale)', 
                         validators=[Optional(), validate_ip_or_network])
    src_port = StringField('Porta Esterna', validators=[DataRequired(), validate_port_or_range])
    dest_ip = StringField('IP Interno', validators=[DataRequired(), validate_ip_or_network])
    dest_port = StringField('Porta Interna', validators=[DataRequired(), validate_port_or_range])
    enabled = BooleanField('Abilitato', default=True)
    submit = SubmitField('Salva Port Forwarding')

    def __init__(self, *args, **kwargs):
        super(FirewallPortForwardingForm, self).__init__(*args, **kwargs)
        # Imposta le zone disponibili (da aggiornare dinamicamente)
        self.source_zone.choices = [('wan', 'WAN'), ('custom', 'Personalizzata')]
        self.dest_zone.choices = [('lan', 'LAN'), ('custom', 'Personalizzata')]

class FirewallIPSetForm(FlaskForm):
    """Form per la creazione/modifica di un IP set"""
    name = StringField('Nome', validators=[
        DataRequired(), 
        Length(min=2, max=64),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Il nome può contenere solo lettere, numeri, trattini e underscore')
    ])
    description = TextAreaField('Descrizione', validators=[Optional(), Length(max=255)])
    type = SelectField('Tipo', choices=[
        ('hash:ip', 'IP singoli'),
        ('hash:net', 'Reti'),
        ('hash:ip,port', 'IP + Porta'),
        ('hash:net,port', 'Rete + Porta')
    ], default='hash:ip')
    addresses = TextAreaField('Indirizzi', validators=[DataRequired()])
    submit = SubmitField('Salva IP Set')

class FirewallServiceGroupForm(FlaskForm):
    """Form per la creazione/modifica di un gruppo di servizi"""
    name = StringField('Nome', validators=[
        DataRequired(), 
        Length(min=2, max=64),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Il nome può contenere solo lettere, numeri, trattini e underscore')
    ])
    description = TextAreaField('Descrizione', validators=[Optional(), Length(max=255)])
    services = TextAreaField('Servizi', validators=[DataRequired()], 
                           render_kw={"placeholder": "tcp:80\nudp:53\ntcp:443\n..."})
    submit = SubmitField('Salva Gruppo Servizi')