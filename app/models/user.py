from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
from datetime import datetime, timedelta
import secrets

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_printer = db.Column(db.Boolean, default=False)

    # New user fields
    country = db.Column(db.String(2), nullable=True, server_default='')
    phone_number = db.Column(db.String(20), nullable=True, server_default='')
    has_seen_welcome = db.Column(db.Boolean, default=False)

    uploads = db.relationship('Upload', backref='author', lazy=True)
    # Orders relationship is managed in the Order model

    # MFA fields
    mfa_secret = db.Column(db.String(32), nullable=True)
    mfa_enabled = db.Column(db.Boolean, default=False)

    # Password reset fields
    reset_token = db.Column(db.String(64), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # JWT refresh token fields
    refresh_token = db.Column(db.String(255), nullable=True)
    refresh_token_expiry = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Properties for template compatibility
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    # MFA methods
    def enable_mfa(self):
        if not self.mfa_secret:
            self.mfa_secret = pyotp.random_base32()
        self.mfa_enabled = True
        
    def disable_mfa(self):
        self.mfa_enabled = False
        
    def verify_totp(self, token):
        if not self.mfa_enabled:
            return True
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token)
        
    def get_totp_uri(self):
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.email,
            issuer_name="VibeDodo"
        )

    def generate_reset_token(self):
        """Generate a secure token for password reset"""
        self.reset_token = secrets.token_hex(32)  # 64 character hex string
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
        return self.reset_token

    def verify_reset_token(self, token):
        """Verify if the provided reset token is valid"""
        # Debug print statements
        print(f"Verifying token: {token[:10]}...")
        print(f"Stored token: {self.reset_token[:10] if self.reset_token else 'None'}...")
        print(f"Token expiry: {self.reset_token_expiry}")
        print(f"Current time: {datetime.utcnow()}")

        if not self.reset_token:
            print("Token verification failed: No token stored")
            return False

        if token != self.reset_token:
            print("Token verification failed: Token mismatch")
            return False

        if self.reset_token_expiry < datetime.utcnow():
            print("Token verification failed: Token expired")
            return False

        print("Token verification successful")
        return True

    def clear_reset_token(self):
        """Clear the reset token after it's been used"""
        self.reset_token = None
        self.reset_token_expiry = None
    
    # JWT methods
    def generate_refresh_token(self):
        """Generate a new refresh token for JWT authentication"""
        self.refresh_token = secrets.token_hex(32)
        self.refresh_token_expiry = datetime.utcnow() + timedelta(days=30)
        return self.refresh_token
    
    def verify_refresh_token(self, token):
        """Verify if the provided refresh token is valid"""
        if not self.refresh_token or not self.refresh_token_expiry:
            return False
        if token != self.refresh_token:
            return False
        if self.refresh_token_expiry < datetime.utcnow():
            return False
        return True
    
    def clear_refresh_token(self):
        """Clear the refresh token on logout"""
        self.refresh_token = None
        self.refresh_token_expiry = None

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
