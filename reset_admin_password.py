#!/usr/bin/env python
# Script per resettare la password dell'utente admin

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Trova l'utente admin
    user = User.query.filter_by(username='admin').first()
    
    if user:
        # Resetta la password
        user.password_hash = generate_password_hash('admin123')
        user.email = 'admin@example.com'  # Aggiorniamo anche l'email se necessario
        db.session.commit()
        print('Password dell\'utente admin resettata con successo')
    else:
        print('Utente admin non trovato')