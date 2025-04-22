from datetime import datetime
from app import db

class DeliveryDay(db.Model):
    """Model for storing available delivery days"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    max_deliveries = db.Column(db.Integer, default=20)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    time_slots = db.relationship('TimeSlot', backref='delivery_day', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"DeliveryDay('{self.date}', active: {self.is_active})"
    
    @property
    def formatted_date(self):
        """Return formatted date string"""
        return self.date.strftime('%A, %B %d, %Y')

class TimeSlot(db.Model):
    """Model for storing available time slots for delivery days"""
    id = db.Column(db.Integer, primary_key=True)
    delivery_day_id = db.Column(db.Integer, db.ForeignKey('delivery_day.id'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    max_orders = db.Column(db.Integer, default=5)
    
    # Relationships - will be added to Order model
    # orders = db.relationship('Order', backref='time_slot', lazy=True)
    
    def __repr__(self):
        return f"TimeSlot('{self.start_time}-{self.end_time}', active: {self.is_active})"
    
    @property
    def formatted_time_range(self):
        """Return formatted time range string"""
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"
    
    @property
    def current_orders_count(self):
        """Return the number of orders assigned to this time slot"""
        from app.models.order import Order
        return Order.query.filter_by(time_slot_id=self.id).count()
    
    @property
    def is_available(self):
        """Check if the slot is available for new orders"""
        if not self.is_active or not self.delivery_day.is_active:
            return False
        return self.current_orders_count < self.max_orders