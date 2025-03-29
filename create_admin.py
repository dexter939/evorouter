#!/usr/bin/env python
# Script per creare un utente admin nel database

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Verifica se l'utente admin esiste già
    user = User.query.filter_by(username='admin').first()
    
    if not user:
        # Crea un nuovo utente admin
        user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        print('Utente admin creato con successo')
    else:
        print('Utente admin già esistente')