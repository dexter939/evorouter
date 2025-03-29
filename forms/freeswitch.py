from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, ValidationError, NumberRange, Regexp

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
    
    voicemail_enabled = BooleanField('Abilita casella vocale', default=True)
    
    voicemail_pin = StringField('PIN Casella Vocale', validators=[
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
