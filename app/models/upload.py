from datetime import datetime
import secrets
import json
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
    text_overlay = db.Column(db.Text, nullable=True)
    
    def generate_share_token(self):
        self.share_token = secrets.token_hex(8)
        self.is_public = True
        return self.share_token
        
    def set_text_overlay(self, text, x, y, font_size, color):
        """Store text overlay information as JSON"""
        overlay_data = {
            'text': text,
            'x': x,
            'y': y,
            'fontSize': font_size,
            'color': color
        }
        self.text_overlay = json.dumps(overlay_data)
        
    def get_text_overlay(self):
        """Get text overlay information as a dictionary"""
        if not self.text_overlay:
            return None
        return json.loads(self.text_overlay)