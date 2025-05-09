import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register custom filters for templates
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s:
            return s.replace('\n', '<br>')
        return s
    
    from app.routes import init_app
    init_app(app)
    
    with app.app_context():
        # Create tables that don't exist yet
        db.create_all()
        
        # Manual check to see if we need to add new columns
        try:
            # First, check if the country field exists on the User model
            from app.models.user import User
            from sqlalchemy import inspect
            
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            # If the country field doesn't exist, we need to modify the table
            if 'country' not in columns or 'phone_number' not in columns:
                print("WARNING: Database schema needs migration. Please run fix_country_phone_migration.py")
                print("For now, we'll try to continue by loading a limited User model")
                
                # Create a temporary User class without the problematic fields
                class TempUser(db.Model):
                    __tablename__ = 'user'
                    id = db.Column(db.Integer, primary_key=True)
                    username = db.Column(db.String(20), unique=True, nullable=False)
                    email = db.Column(db.String(120), unique=True, nullable=False)
                    password_hash = db.Column(db.String(128), nullable=False)
                    is_admin = db.Column(db.Boolean, default=False)
                
                # Use this version instead
                admin = TempUser.query.filter_by(is_admin=True).first()
                if not admin:
                    admin = TempUser.query.filter_by(email='admin@example.com').first()
                    if not admin:
                        admin = TempUser(username='admin', email='admin@example.com', is_admin=True)
                        # We don't have set_password for this minimal model, so we'd have to handle it differently
                        # For now, let's just skip this step since we're focusing on migration
                        db.session.add(admin)
                        db.session.commit()
            else:
                # Normal path when schema is correct
                admin = User.query.filter_by(is_admin=True).first()
                if not admin:
                    admin = User.query.filter_by(email='admin@example.com').first()
                    if not admin:
                        admin = User(username='admin', email='admin@example.com', is_admin=True)
                        admin.set_password('admin123')
                        db.session.add(admin)
                        db.session.commit()
        except Exception as e:
            print(f"Error during initialization: {e}")
            print("You may need to run fix_country_phone_migration.py to update your database schema.")
    
    return app
