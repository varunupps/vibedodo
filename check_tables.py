#!/usr/bin/env python3
from app import create_app, db
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables in the database:")
    for table in tables:
        print(f"- {table}")
        
    # Also print the Order model's __tablename__ attribute
    from app.models.order import Order
    print(f"\nOrder table name: {Order.__tablename__ if hasattr(Order, '__tablename__') else 'order'}")