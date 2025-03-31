import os
import logging
from pathlib import Path
import sys

from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carica variabili d'ambiente dal file .env se esiste
env_file = Path('.env')
if env_file.exists():
    logger.info(f"Caricamento variabili d'ambiente da {env_file.absolute()}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ[key] = value
    logger.info("Variabili d'ambiente caricate con successo")
else:
    logger.info("File .env non trovato, utilizzo delle variabili d'ambiente di sistema")

# Create a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Create Flask application
app = Flask(__name__)

# Configure application secret key
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Configure database URI
database_url = os.environ.get("DATABASE_URL", "sqlite:///evorouter.db")
# Fix PostgreSQL connection string for SQLAlchemy if needed
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", app.secret_key)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hour
jwt = JWTManager(app)

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Effettua l'accesso per visualizzare questa pagina."

# Initialize CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)

# Import and register blueprints
from routes.dashboard import dashboard_bp
from routes.network import network_bp
from routes.system import system_bp
from routes.auth import auth_bp
from routes.api import api_bp
from routes.freeswitch import freeswitch_bp
from routes.freeswitch_install import freeswitch_install_bp
from routes.vpn import vpn
from routes.upnp import upnp_bp
from routes.firewall import firewall
from routes.qos import qos
from routes.payments import payments_bp

app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(network_bp, url_prefix='/network')
app.register_blueprint(system_bp, url_prefix='/system')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(freeswitch_bp, url_prefix='/freeswitch')
app.register_blueprint(freeswitch_install_bp, url_prefix='/freeswitch')
app.register_blueprint(vpn, url_prefix='/vpn')
app.register_blueprint(firewall, url_prefix='/firewall')
app.register_blueprint(upnp_bp, url_prefix='/firewall/upnp')
app.register_blueprint(qos, url_prefix='/qos')
app.register_blueprint(payments_bp, url_prefix='/payments')

# Import user loader
from models import User

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    
    # Create default admin user if no users exist
    if not User.query.first():
        from werkzeug.security import generate_password_hash
        default_admin = User(
            username="admin",
            email="admin@localhost",
            password_hash=generate_password_hash("admin"),
            is_admin=True
        )
        db.session.add(default_admin)
        db.session.commit()
        logger.info("Created default admin user")

logger.info("Application initialized")

# Add a route for the root URL that redirects to the dashboard
@app.route('/')
def index():
    return redirect(url_for('dashboard.index'))
