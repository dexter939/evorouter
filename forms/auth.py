from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricordami')
    submit = SubmitField('Login')

class ChangePasswordForm(FlaskForm):
    """Form for changing password"""
    current_password = PasswordField('Password attuale', validators=[DataRequired()])
    new_password = PasswordField('Nuova password', validators=[
        DataRequired(),
        Length(min=8, message='La password deve essere lunga almeno 8 caratteri')
    ])
    confirm_password = PasswordField('Conferma nuova password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Le password non corrispondono')
    ])
    submit = SubmitField('Cambia Password')
    
    def validate_new_password(self, new_password):
        """Validate password strength"""
        password = new_password.data
        
        if not any(c.isupper() for c in password):
            raise ValidationError('La password deve contenere almeno una lettera maiuscola')
        
        if not any(c.islower() for c in password):
            raise ValidationError('La password deve contenere almeno una lettera minuscola')
        
        if not any(c.isdigit() for c in password):
            raise ValidationError('La password deve contenere almeno un numero')
        
        if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for c in password):
            raise ValidationError('La password deve contenere almeno un carattere speciale')
