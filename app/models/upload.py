from datetime import datetime
import secrets
import json
from app import db

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(150), nullable=False)
    caption = db.Column(db.String(500), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    share_token = db.Column(db.String(16), unique=True, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    text_overlay = db.Column(db.Text, nullable=True, server_default=None)
    classification = db.Column(db.String(20), nullable=True, server_default=None)
    is_mock_classified = db.Column(db.Boolean, default=False)
    
    def generate_share_token(self):
        self.share_token = secrets.token_hex(8)
        self.is_public = True
        return self.share_token
        
    def set_text_overlay(self, text, x, y, font_size, color):
        """Store text overlay information as JSON"""
        try:
            overlay_data = {
                'text': text,
                'x': x,
                'y': y,
                'fontSize': font_size,
                'color': color
            }
            json_data = json.dumps(overlay_data)
            print(f"Setting text_overlay to: {json_data}")
            self.text_overlay = json_data
            print(f"After setting, text_overlay is: {self.text_overlay}")
        except Exception as e:
            print(f"Error in set_text_overlay: {str(e)}")
            raise
        
    def get_text_overlay(self):
        """Get text overlay information as a dictionary"""
        try:
            if not self.text_overlay:
                print(f"Upload ID {self.id}: No text overlay found")
                return None
            
            overlay_data = json.loads(self.text_overlay)
            print(f"Upload ID {self.id}: Successfully loaded overlay data: {overlay_data}")
            return overlay_data
        except Exception as e:
            print(f"Upload ID {self.id}: Error getting text overlay: {str(e)}")
            return None