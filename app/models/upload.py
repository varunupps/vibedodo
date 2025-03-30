from datetime import datetime
import secrets
from app import db
from flask_login import UserMixin

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(150), nullable=False)
    caption = db.Column(db.String(500), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    share_token = db.Column(db.String(16), unique=True, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    
    def generate_share_token(self):
        self.share_token = secrets.token_hex(8)
        self.is_public = True
        return self.share_token