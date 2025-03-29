from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, IntegerField, SubmitField, EmailField, SelectField
from wtforms.validators import DataRequired, Optional, Length, ValidationError, NumberRange, Regexp, Email

class ExtensionForm(FlaskForm):
    """Form for managing FreeSWITCH extensions"""
    extension_number = StringField('Numero Estensione', validators=[
        DataRequired(message='Il numero estensione è obbligatorio'),
        Regexp('^\d{3,6}$', message='Il numero estensione deve essere composto da 3-6 cifre')
    ])
    
    name = StringField('Nome', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=2, max=64, message='Il nome deve essere lungo tra 2 e 64 caratteri')
    ])
    
    password = PasswordField('Password', validators=[
        Optional(),
        Length(min=8, max=64, message='La password deve essere lunga almeno 8 caratteri')
    ])
    
    # Caller ID settings
    caller_id_name = StringField('Nome Chiamante (Caller ID)', validators=[
        Optional(),
        Length(max=64, message='Il nome del chiamante non può superare i 64 caratteri')
    ])
    
    caller_id_number = StringField('Numero Chiamante (Caller ID)', validators=[
        Optional(),
        Length(max=32, message='Il numero del chiamante non può superare i 32 caratteri'),
        Regexp('^\d*$', message='Il numero del chiamante deve essere composto solo da cifre')
    ])
    
    # Voicemail settings
    voicemail_enabled = BooleanField('Abilita casella vocale', default=True)
    
    voicemail_pin = StringField('PIN Casella Vocale', validators=[
        Optional(),
        Regexp('^\d{4,10}$', message='Il PIN deve essere composto da 4-10 cifre numeriche')
    ])
    
    voicemail_email = EmailField('Email per notifiche voicemail', validators=[
        Optional(),
        Email(message='Inserisci un indirizzo email valido')
    ])
    
    voicemail_attach_file = BooleanField('Allega file audio alle email', default=True)
    
    voicemail_delete_after_email = BooleanField('Cancella messaggio dopo invio email', default=False)
    
    # Call recording settings
    record_inbound = BooleanField('Registra chiamate in entrata', default=False)
    
    record_outbound = BooleanField('Registra chiamate in uscita', default=False)
    
    # Hot desking
    hot_desk_enabled = BooleanField('Abilita Hot Desking', default=False)
    
    hot_desk_pin = StringField('PIN Hot Desking', validators=[
        Optional(),
        Regexp('^\d{4,10}$', message='Il PIN deve essere composto da 4-10 cifre numeriche')
    ])
    
    submit = SubmitField('Salva Estensione')
    
    def validate(self):
        """Custom validation logic"""
        if not super().validate():
            return False
            
        # If voicemail is enabled, PIN is required
        if self.voicemail_enabled.data and not self.voicemail_pin.data:
            self.voicemail_pin.errors = ['Il PIN è obbligatorio quando la casella vocale è abilitata']
            return False
            
        # If hot desking is enabled, PIN is required
        if self.hot_desk_enabled.data and not self.hot_desk_pin.data:
            self.hot_desk_pin.errors = ['Il PIN è obbligatorio quando Hot Desking è abilitato']
            return False
            
        return True
    
    def validate_password(self, field):
        """Validate password strength"""
        if field.data:
            # Skip empty passwords (for edit form)
            if len(field.data) < 8:
                raise ValidationError('La password deve essere lunga almeno 8 caratteri')
                
            # Basic strength validation
            has_upper = any(c.isupper() for c in field.data)
            has_lower = any(c.islower() for c in field.data)
            has_digit = any(c.isdigit() for c in field.data)
            has_special = any(c for c in field.data if not c.isalnum())
            
            if not (has_upper and has_lower and has_digit):
                raise ValidationError('La password deve contenere almeno una lettera maiuscola, una minuscola e un numero')
                
            if not has_special:
                raise ValidationError('La password deve contenere almeno un carattere speciale')

class TrunkForm(FlaskForm):
    """Form for managing FreeSWITCH SIP trunks"""
    name = StringField('Nome Trunk', validators=[
        DataRequired(message='Il nome del trunk è obbligatorio'),
        Length(min=2, max=64, message='Il nome deve essere lungo tra 2 e 64 caratteri')
    ])
    
    host = StringField('Host/IP Provider', validators=[
        DataRequired(message='L\'host è obbligatorio'),
        Length(min=2, max=128, message='L\'host deve essere lungo tra 2 e 128 caratteri')
    ])
    
    port = IntegerField('Porta', validators=[
        Optional(),
        NumberRange(min=1, max=65535, message='La porta deve essere tra 1 e 65535')
    ], default=5060)
    
    username = StringField('Nome Utente', validators=[
        Optional(),
        Length(max=64, message='Il nome utente non può superare i 64 caratteri')
    ])
    
    password = PasswordField('Password', validators=[
        Optional(),
        Length(max=64, message='La password non può superare i 64 caratteri')
    ])
    
    enabled = BooleanField('Trunk attivo', default=True)
    
    submit = SubmitField('Salva Trunk')

class IvrMenuForm(FlaskForm):
    """Form for managing IVR menus"""
    name = StringField('Nome Menu IVR', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=2, max=64, message='Il nome deve essere lungo tra 2 e 64 caratteri')
    ])
    
    description = StringField('Descrizione', validators=[
        Optional(),
        Length(max=255, message='La descrizione non può superare i 255 caratteri')
    ])
    
    greeting_message = StringField('Messaggio di Benvenuto', validators=[
        DataRequired(message='Il messaggio di benvenuto è obbligatorio'),
        Length(min=10, max=512, message='Il messaggio deve essere lungo tra 10 e 512 caratteri')
    ])
    
    timeout = IntegerField('Timeout (secondi)', validators=[
        NumberRange(min=3, max=60, message='Il timeout deve essere tra 3 e 60 secondi')
    ], default=10)
    
    max_failures = IntegerField('Tentativi massimi', validators=[
        NumberRange(min=1, max=10, message='I tentativi massimi devono essere tra 1 e 10')
    ], default=3)
    
    enabled = BooleanField('Menu attivo', default=True)
    
    submit = SubmitField('Salva Menu IVR')

class IvrOptionForm(FlaskForm):
    """Form for managing IVR menu options"""
    digit = SelectField('Tasto', choices=[
        ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), 
        ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), 
        ('*', '*'), ('#', '#')
    ], validators=[DataRequired(message='Seleziona un tasto')])
    
    action_type = SelectField('Azione', choices=[
        ('extension', 'Interno SIP'),
        ('voicemail', 'Casella Vocale'),
        ('queue', 'Coda di Chiamata'),
        ('submenu', 'Sottomenu IVR'),
        ('time_condition', 'Condizione Temporale'),
        ('hangup', 'Riaggancia'),
        ('playback', 'Riproduci Audio')
    ], validators=[DataRequired(message='Seleziona un\'azione')])
    
    action_data = StringField('Dati Azione', validators=[
        DataRequired(message='I dati dell\'azione sono obbligatori'),
        Length(max=128, message='I dati non possono superare i 128 caratteri')
    ])
    
    description = StringField('Descrizione', validators=[
        Optional(),
        Length(max=255, message='La descrizione non può superare i 255 caratteri')
    ])
    
    submit = SubmitField('Aggiungi Opzione')

class CallQueueForm(FlaskForm):
    """Form for managing call queues"""
    name = StringField('Nome Coda', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=2, max=64, message='Il nome deve essere lungo tra 2 e 64 caratteri')
    ])
    
    strategy = SelectField('Strategia di Distribuzione', choices=[
        ('round-robin', 'Round Robin'),
        ('ring-all', 'Chiama Tutti'),
        ('least-recent', 'Meno Recente'),
        ('fewest-calls', 'Meno Chiamate'),
        ('random', 'Casuale'),
        ('skill-based', 'Basata su Abilità')
    ], validators=[DataRequired(message='Seleziona una strategia')])
    
    moh_class = StringField('Classe Musica di Attesa', validators=[
        Optional(),
        Length(max=64, message='La classe non può superare i 64 caratteri')
    ], default='default')
    
    announce_position = BooleanField('Annuncia posizione in coda', default=False)
    
    announce_holdtime = BooleanField('Annuncia tempo di attesa stimato', default=False)
    
    max_wait_time = IntegerField('Tempo massimo di attesa (secondi)', validators=[
        NumberRange(min=30, max=3600, message='Il tempo di attesa deve essere tra 30 e 3600 secondi')
    ], default=300)
    
    max_callers = IntegerField('Chiamanti massimi in coda', validators=[
        NumberRange(min=1, max=100, message='Il numero di chiamanti deve essere tra 1 e 100')
    ], default=10)
    
    timeout = IntegerField('Timeout agente (secondi)', validators=[
        NumberRange(min=5, max=120, message='Il timeout deve essere tra 5 e 120 secondi')
    ], default=60)
    
    wrapup_time = IntegerField('Tempo di preparazione agente (secondi)', validators=[
        NumberRange(min=0, max=120, message='Il tempo di preparazione deve essere tra 0 e 120 secondi')
    ], default=5)
    
    enabled = BooleanField('Coda attiva', default=True)
    
    submit = SubmitField('Salva Coda')

class QueueMemberForm(FlaskForm):
    """Form for managing queue members"""
    extension_id = SelectField('Interno', validators=[
        DataRequired(message='Seleziona un interno')
    ], coerce=int)
    
    priority = IntegerField('Priorità (1-10)', validators=[
        NumberRange(min=1, max=10, message='La priorità deve essere tra 1 e 10')
    ], default=1)
    
    penalty = IntegerField('Penalità (0-10)', validators=[
        NumberRange(min=0, max=10, message='La penalità deve essere tra 0 e 10')
    ], default=0)
    
    submit = SubmitField('Aggiungi Agente')
    
    def __init__(self, *args, **kwargs):
        super(QueueMemberForm, self).__init__(*args, **kwargs)
        from models import SipExtension
        from app import db
        
        # Populate extension choices dynamically
        extensions = db.session.query(SipExtension).all()
        self.extension_id.choices = [(ext.id, f"{ext.extension_number} - {ext.name}") for ext in extensions]

class TimeConditionForm(FlaskForm):
    """Form for managing time conditions"""
    name = StringField('Nome Condizione', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=2, max=64, message='Il nome deve essere lungo tra 2 e 64 caratteri')
    ])
    
    days_of_week = SelectField('Giorni della Settimana', choices=[
        ('0,1,2,3,4,5,6', 'Tutti i giorni'),
        ('1,2,3,4,5', 'Giorni feriali (Lun-Ven)'),
        ('0,6', 'Fine settimana (Dom, Sab)'),
        ('0', 'Domenica'),
        ('1', 'Lunedì'),
        ('2', 'Martedì'),
        ('3', 'Mercoledì'),
        ('4', 'Giovedì'),
        ('5', 'Venerdì'),
        ('6', 'Sabato')
    ], validators=[DataRequired(message='Seleziona i giorni')])
    
    time_start = StringField('Ora Inizio (HH:MM)', validators=[
        DataRequired(message='L\'ora di inizio è obbligatoria'),
        Regexp('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', message='Formato ora non valido (HH:MM)')
    ])
    
    time_end = StringField('Ora Fine (HH:MM)', validators=[
        DataRequired(message='L\'ora di fine è obbligatoria'),
        Regexp('^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', message='Formato ora non valido (HH:MM)')
    ])
    
    destination_match = SelectField('Destinazione', choices=[
        ('extension', 'Interno SIP'),
        ('ivr', 'Menu IVR'),
        ('queue', 'Coda di Chiamata'),
        ('voicemail', 'Casella Vocale'),
        ('hangup', 'Riaggancia')
    ], validators=[DataRequired(message='Seleziona una destinazione')])
    
    destination_match_id = StringField('ID Destinazione', validators=[
        DataRequired(message='L\'ID della destinazione è obbligatorio')
    ])
    
    fallback_destination = SelectField('Destinazione Fallback', choices=[
        ('', 'Nessuna'),
        ('extension', 'Interno SIP'),
        ('ivr', 'Menu IVR'),
        ('queue', 'Coda di Chiamata'),
        ('voicemail', 'Casella Vocale'),
        ('hangup', 'Riaggancia')
    ])
    
    fallback_destination_id = StringField('ID Destinazione Fallback')
    
    enabled = BooleanField('Condizione attiva', default=True)
    
    submit = SubmitField('Salva Condizione')
    
    def validate(self):
        """Custom validation logic"""
        if not super().validate():
            return False
        
        # If fallback destination is selected, ID is required
        if self.fallback_destination.data and not self.fallback_destination.data == '':
            if not self.fallback_destination_id.data:
                self.fallback_destination_id.errors = ['L\'ID della destinazione fallback è obbligatorio']
                return False
                
        return True

class InboundRouteForm(FlaskForm):
    """Form for managing inbound call routes"""
    name = StringField('Nome Regola', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=2, max=64, message='Il nome deve essere lungo tra 2 e 64 caratteri')
    ])
    
    did_number = StringField('Numero DID/DDI', validators=[
        DataRequired(message='Il numero DID è obbligatorio'),
        Length(min=3, max=32, message='Il numero deve essere lungo tra 3 e 32 caratteri'),
        Regexp('^\d+$', message='Il numero deve essere composto solo da cifre')
    ])
    
    trunk_id = SelectField('Trunk SIP', coerce=int)
    
    destination_type = SelectField('Tipo Destinazione', choices=[
        ('extension', 'Interno SIP'),
        ('ivr', 'Menu IVR'),
        ('queue', 'Coda di Chiamata'),
        ('time_condition', 'Condizione Temporale'),
        ('voicemail', 'Casella Vocale')
    ], validators=[DataRequired(message='Seleziona un tipo di destinazione')])
    
    destination_id = StringField('ID Destinazione', validators=[
        DataRequired(message='L\'ID della destinazione è obbligatorio')
    ])
    
    enabled = BooleanField('Regola attiva', default=True)
    
    submit = SubmitField('Salva Regola')
    
    def __init__(self, *args, **kwargs):
        super(InboundRouteForm, self).__init__(*args, **kwargs)
        from models import SipTrunk
        from app import db
        
        # Populate trunk choices dynamically
        trunks = db.session.query(SipTrunk).all()
        self.trunk_id.choices = [(0, 'Qualsiasi Trunk')] + [(t.id, t.name) for t in trunks]

class OutboundRouteForm(FlaskForm):
    """Form for managing outbound call routes"""
    name = StringField('Nome Regola', validators=[
        DataRequired(message='Il nome è obbligatorio'),
        Length(min=2, max=64, message='Il nome deve essere lungo tra 2 e 64 caratteri')
    ])
    
    pattern = StringField('Pattern di Corrispondenza', validators=[
        DataRequired(message='Il pattern è obbligatorio'),
        Length(min=1, max=64, message='Il pattern deve essere lungo tra 1 e 64 caratteri')
    ])
    
    trunk_id = SelectField('Trunk SIP', validators=[
        DataRequired(message='Seleziona un trunk')
    ], coerce=int)
    
    priority = IntegerField('Priorità', validators=[
        NumberRange(min=1, max=100, message='La priorità deve essere tra 1 e 100')
    ], default=1)
    
    prefix = StringField('Prefisso da Aggiungere', validators=[
        Optional(),
        Length(max=16, message='Il prefisso non può superare i 16 caratteri'),
        Regexp('^\d*$', message='Il prefisso deve essere composto solo da cifre')
    ])
    
    strip = IntegerField('Cifre da Rimuovere', validators=[
        NumberRange(min=0, max=16, message='Il numero di cifre deve essere tra 0 e 16')
    ], default=0)
    
    enabled = BooleanField('Regola attiva', default=True)
    
    submit = SubmitField('Salva Regola')
    
    def __init__(self, *args, **kwargs):
        super(OutboundRouteForm, self).__init__(*args, **kwargs)
        from models import SipTrunk
        from app import db
        
        # Populate trunk choices dynamically
        trunks = db.session.query(SipTrunk).filter_by(enabled=True).all()
        self.trunk_id.choices = [(t.id, t.name) for t in trunks]

class BlacklistForm(FlaskForm):
    """Form for managing blacklisted numbers"""
    number = StringField('Numero da Bloccare', validators=[
        DataRequired(message='Il numero è obbligatorio'),
        Length(min=3, max=32, message='Il numero deve essere lungo tra 3 e 32 caratteri'),
        Regexp('^\d+$', message='Il numero deve essere composto solo da cifre')
    ])
    
    description = StringField('Descrizione', validators=[
        Optional(),
        Length(max=255, message='La descrizione non può superare i 255 caratteri')
    ])
    
    submit = SubmitField('Aggiungi a Blacklist')
