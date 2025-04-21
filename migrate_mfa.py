from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sys

# Create a minimal app instance just for migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/varun/Desktop/sample_apps/vibedodo/instance/site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def upgrade():
    with app.app_context():
        # Add MFA columns to User model
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE user ADD COLUMN mfa_secret VARCHAR(32)'))
                conn.execute(db.text('ALTER TABLE user ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0'))
                conn.commit()
            
            print("Database migrated successfully with MFA fields")
        except Exception as e:
            print(f"Error during migration: {e}")
            print("If the columns already exist, you can ignore this error.")

if __name__ == '__main__':
    upgrade()