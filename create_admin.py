#!/usr/bin/env python
# Script per creare un utente admin nel database
import os
import sys
import logging

# Configurazione del logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Verifica preliminare del database SQLite
db_url = os.environ.get("DATABASE_URL", "")
if db_url.startswith("sqlite:///"):
    db_path = db_url.replace("sqlite:///", "")
    
    # Se il percorso è relativo, assumiamo che sia relativo alla directory corrente
    if not db_path.startswith("/"):
        db_path = os.path.join(os.getcwd(), "instance", db_path)
    else:
        # Assicuriamoci che la directory esista
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                os.chmod(db_dir, 0o777)
                logger.info(f"Creata directory {db_dir} con permessi 777")
            except Exception as e:
                logger.error(f"Impossibile creare la directory {db_dir}: {str(e)}")
                sys.exit(1)
    
    # Verifica se il file del database esiste e se la directory è scrivibile
    try:
        # Assicurati che il file db esista
        if not os.path.exists(db_path):
            logger.info(f"Il file del database {db_path} non esiste, tentativo di creazione...")
            try:
                # Assicurati che la directory esista
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                # Crea un file vuoto
                with open(db_path, 'w'):
                    pass
                os.chmod(db_path, 0o666)  # Permessi di lettura/scrittura per tutti
                logger.info(f"File del database creato in {db_path} con permessi 666")
            except Exception as e:
                logger.error(f"Impossibile creare il file del database: {str(e)}")
        
        # Verifica i permessi del file
        if not os.access(db_path, os.W_OK):
            logger.warning(f"Il file del database {db_path} non è scrivibile, tentativo di correzione...")
            try:
                os.chmod(db_path, 0o666)
                logger.info(f"Permessi del database modificati a 666")
            except Exception as e:
                logger.error(f"Impossibile modificare i permessi del database: {str(e)}")
    except Exception as e:
        logger.error(f"Errore durante la verifica/creazione del database SQLite: {str(e)}")

try:
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
            logger.info('Utente admin creato con successo')
        else:
            logger.info('Utente admin già esistente')
except Exception as e:
    logger.error(f"Errore durante la creazione dell'utente admin: {str(e)}")
    sys.exit(1)