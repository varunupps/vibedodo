from datetime import datetime
from app import db

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    date_ordered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Status options: pending, approved_for_printing, printed, shipped, completed
    status = db.Column(db.String(20), default='pending', nullable=False)
    
    # Printer specific fields
    approved_for_printing = db.Column(db.Boolean, default=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    printed = db.Column(db.Boolean, default=False)
    printed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    printed_date = db.Column(db.DateTime, nullable=True)
    
    # Additional notes for printing
    print_notes = db.Column(db.String(500), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='orders')
    upload = db.relationship('Upload', backref='orders')
    approved_by = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_orders')
    printed_by = db.relationship('User', foreign_keys=[printed_by_id], backref='printed_orders')
    
    def __repr__(self):
        return f"Order(ID: {self.id}, User: {self.user_id}, Status: {self.status})"