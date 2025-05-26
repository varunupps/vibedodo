#!/usr/bin/env python3
"""
Migration script to add JWT refresh token fields to the User table
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def migrate_jwt_fields():
    """Add refresh token fields to User table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Add refresh_token column
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE user ADD COLUMN refresh_token VARCHAR(255)'))
                conn.commit()
            print("✓ Added refresh_token column")
        except Exception as e:
            print(f"refresh_token column might already exist: {e}")
        
        try:
            # Add refresh_token_expiry column
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE user ADD COLUMN refresh_token_expiry DATETIME'))
                conn.commit()
            print("✓ Added refresh_token_expiry column")
        except Exception as e:
            print(f"refresh_token_expiry column might already exist: {e}")
        
        print("✓ JWT migration completed successfully!")

if __name__ == '__main__':
    migrate_jwt_fields()