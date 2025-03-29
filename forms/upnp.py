from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, IPAddress


class UPnPConfigForm(FlaskForm):
    """Form per la configurazione UPnP"""
    enabled = BooleanField('Abilita UPnP')
    secure_mode = BooleanField('Modalità sicura (solo LAN)', default=True)
    allow_remote_host = BooleanField('Consenti richieste da host remoti')
    allow_loopback = BooleanField('Consenti richieste da localhost')
    
    internal_port_range_start = IntegerField('Porta interna iniziale', 
                                           validators=[NumberRange(min=1, max=65535)],
                                           default=1024)
    internal_port_range_end = IntegerField('Porta interna finale', 
                                         validators=[NumberRange(min=1, max=65535)],
                                         default=65535)
    external_port_range_start = IntegerField('Porta esterna iniziale', 
                                           validators=[NumberRange(min=1, max=65535)],
                                           default=1024)
    external_port_range_end = IntegerField('Porta esterna finale', 
                                         validators=[NumberRange(min=1, max=65535)],
                                         default=65535)
    
    max_lease_duration = IntegerField('Durata massima lease (secondi)', 
                                    validators=[NumberRange(min=0)],
                                    default=86400)
    notify_interval = IntegerField('Intervallo di notifica (secondi)', 
                                 validators=[NumberRange(min=30, max=86400)],
                                 default=1800)
    
    submit = SubmitField('Salva configurazione')


class UPnPPortMappingForm(FlaskForm):
    """Form per l'aggiunta di port mapping UPnP"""
    description = StringField('Descrizione', 
                            validators=[Length(max=128)],
                            render_kw={"placeholder": "Descrizione del servizio"})
    
    external_port = IntegerField('Porta esterna', 
                               validators=[DataRequired(), NumberRange(min=1, max=65535)],
                               render_kw={"placeholder": "Porta esterna (1-65535)"})
    
    internal_port = IntegerField('Porta interna', 
                               validators=[DataRequired(), NumberRange(min=1, max=65535)],
                               render_kw={"placeholder": "Porta interna (1-65535)"})
    
    internal_client = StringField('IP client interno', 
                                validators=[DataRequired(), IPAddress()],
                                render_kw={"placeholder": "192.168.1.x"})
    
    protocol = SelectField('Protocollo', 
                         choices=[('TCP', 'TCP'), ('UDP', 'UDP')],
                         default='TCP')
    
    lease_duration = IntegerField('Durata lease (secondi, 0=permanente)', 
                                validators=[NumberRange(min=0)],
                                default=0)
    
    remote_host = StringField('Host remoto (vuoto = tutti)', 
                            validators=[Optional(), Length(max=64)],
                            render_kw={"placeholder": "Vuoto o IP specifico"})
    
    enabled = BooleanField('Abilitato', default=True)
    
    submit = SubmitField('Aggiungi port mapping')