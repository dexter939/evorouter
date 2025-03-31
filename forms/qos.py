"""
Forms per la gestione del Quality of Service (QoS).
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError, Regexp
import ipaddress
from forms.firewall import validate_ip_or_network, validate_port_or_range

class QoSConfigForm(FlaskForm):
    """Form per la configurazione principale del QoS"""
    enabled = BooleanField('Abilita QoS', default=False)
    interface = SelectField('Interfaccia', validators=[DataRequired()])
    download_bandwidth = IntegerField('Banda Download (kbps)', 
                                   validators=[DataRequired(), NumberRange(min=1, max=1000000)],
                                   description="Larghezza di banda massima in download in kilobit al secondo")
    upload_bandwidth = IntegerField('Banda Upload (kbps)', 
                                 validators=[DataRequired(), NumberRange(min=1, max=1000000)],
                                 description="Larghezza di banda massima in upload in kilobit al secondo")
    default_class = StringField('Classe Predefinita', 
                             validators=[DataRequired(), Length(min=2, max=32)],
                             default='default',
                             description="Nome della classe per il traffico non classificato")
    hierarchical = BooleanField('Modalità Gerarchica', default=True, 
                             description="Utilizza HTB (hierarchical token bucket) per la gestione della banda")
    submit = SubmitField('Salva Configurazione')
    
    def __init__(self, *args, **kwargs):
        super(QoSConfigForm, self).__init__(*args, **kwargs)
        # Popolamento dinamico delle interfacce
        self.interface.choices = [('wan', 'WAN'), ('lan', 'LAN'), ('eth0', 'ETH0'), ('eth1', 'ETH1')]

class QoSClassForm(FlaskForm):
    """Form per la creazione/modifica di una classe di traffico QoS"""
    name = StringField('Nome', validators=[
        DataRequired(), 
        Length(min=2, max=32),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Il nome può contenere solo lettere, numeri, trattini e underscore')
    ])
    description = TextAreaField('Descrizione', validators=[Optional(), Length(max=255)])
    priority = SelectField('Priorità', choices=[
        (1, '1 - Altissima'),
        (2, '2 - Alta'),
        (3, '3 - Medio-alta'),
        (4, '4 - Media'),
        (5, '5 - Medio-bassa'),
        (6, '6 - Bassa'),
        (7, '7 - Bassissima')
    ], coerce=int, default=4)
    min_bandwidth = IntegerField('Banda Minima (%)', 
                              validators=[NumberRange(min=0, max=100)],
                              default=0,
                              description="Percentuale minima di banda garantita")
    max_bandwidth = IntegerField('Banda Massima (%)', 
                              validators=[NumberRange(min=1, max=100)],
                              default=100,
                              description="Percentuale massima di banda utilizzabile")
    submit = SubmitField('Salva Classe')
    
    def validate_max_bandwidth(self, field):
        """Validazione per assicurarsi che la banda massima sia maggiore della minima"""
        if field.data < self.min_bandwidth.data:
            raise ValidationError('La banda massima deve essere maggiore o uguale alla banda minima')

class QoSRuleForm(FlaskForm):
    """Form per la creazione/modifica di una regola QoS"""
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=64)])
    description = TextAreaField('Descrizione', validators=[Optional(), Length(max=255)])
    class_id = SelectField('Classe di Traffico', coerce=int, validators=[DataRequired()])
    source = StringField('Origine (opzionale)', 
                      validators=[Optional(), validate_ip_or_network],
                      description="IP o rete sorgente (es. 192.168.1.10 o 192.168.1.0/24)")
    destination = StringField('Destinazione (opzionale)', 
                           validators=[Optional(), validate_ip_or_network],
                           description="IP o rete destinazione (es. 8.8.8.8 o 10.0.0.0/8)")
    protocol = SelectField('Protocollo', choices=[
        ('all', 'Tutti i protocolli'),
        ('tcp', 'TCP'),
        ('udp', 'UDP'),
        ('icmp', 'ICMP'),
        ('tcp,udp', 'TCP+UDP')
    ], default='all')
    src_port = StringField('Porta Origine (opzionale)', 
                        validators=[Optional(), validate_port_or_range],
                        description="Porta singola (80), intervallo (1000-2000) o elenco (80,443,8080)")
    dst_port = StringField('Porta Destinazione (opzionale)', 
                        validators=[Optional(), validate_port_or_range],
                        description="Porta singola (80), intervallo (1000-2000) o elenco (80,443,8080)")
    dscp = StringField('DSCP (opzionale)', 
                     validators=[Optional(), Length(max=16)],
                     description="Differentiated Services Code Point (es. EF, AF11, CS7)")
    direction = SelectField('Direzione', choices=[
        ('both', 'Entrambe le direzioni'),
        ('in', 'Solo traffico in ingresso'),
        ('out', 'Solo traffico in uscita')
    ], default='both')
    priority = IntegerField('Priorità Regola', 
                         validators=[NumberRange(min=0, max=999)],
                         default=0,
                         description="Valore più basso = priorità maggiore")
    enabled = BooleanField('Abilitata', default=True)
    submit = SubmitField('Salva Regola')
    
    def __init__(self, *args, **kwargs):
        super(QoSRuleForm, self).__init__(*args, **kwargs)
        # Nota: il popolamento delle classi dovrebbe essere fatto prima del rendering del form