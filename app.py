import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from flask_jwt_extended import JWTManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
database_url = os.environ.get("DATABASE_URL", "sqlite:///bpir4_router.db")
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

# Import and register blueprints
from routes.dashboard import dashboard_bp
from routes.network import network_bp
from routes.freeswitch import freeswitch_bp
from routes.system import system_bp
from routes.auth import auth_bp
from routes.api import api_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(network_bp, url_prefix='/network')
app.register_blueprint(freeswitch_bp, url_prefix='/freeswitch')
app.register_blueprint(system_bp, url_prefix='/system')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_bp, url_prefix='/api')

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
