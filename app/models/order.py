from datetime import datetime
from app import db

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    date_ordered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, shipped, completed
    
    # Relationships
    user = db.relationship('User', backref='orders')
    upload = db.relationship('Upload', backref='orders')
    
    def __repr__(self):
        return f"Order(ID: {self.id}, User: {self.user_id}, Status: {self.status})"