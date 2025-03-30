from app import create_app, db
import os
import sqlite3
from datetime import datetime
import json

def backup_and_recreate_db():
    """
    This script will:
    1. Back up the current database
    2. Extract all data from the current tables
    3. Drop all tables
    4. Recreate the schema with the updated models
    5. Reinsert the data
    """
    app = create_app()
    
    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if db_path.startswith('/'):
            # Absolute path
            backup_path = f"{db_path}.backup"
        else:
            # Relative path
            backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{db_path}.backup")
        
        print(f"Database path: {db_path}")
        
        # 1. Create a backup of the current database
        if os.path.exists(db_path):
            import shutil
            shutil.copyfile(db_path, backup_path)
            print(f"Created backup at {backup_path}")
        
        # 2. Extract data from current tables
        data = {}
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Get list of tables
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        table_names = [table['name'] for table in tables if table['name'] != 'sqlite_sequence']
        
        # Extract data from each table
        for table in table_names:
            try:
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
                data[table] = [dict(row) for row in rows]
                print(f"Extracted {len(data[table])} rows from {table}")
            except sqlite3.OperationalError as e:
                print(f"Error extracting data from {table}: {str(e)}")
        
        conn.close()
        
        # 3. Drop all tables and recreate with the new schema
        db.drop_all()
        print("Dropped all tables")
        
        db.create_all()
        print("Created tables with new schema")
        
        # 4. Reinsert data
        from app.models.user import User
        from app.models.upload import Upload
        from app.models.order import Order
        
        # Insert users
        if 'user' in data:
            for user_data in data['user']:
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    is_admin=bool(user_data['is_admin'])
                )
                db.session.add(user)
            print(f"Inserted {len(data.get('user', []))} users")
        
        # Insert uploads (with new fields initialized)
        if 'upload' in data:
            for upload_data in data['upload']:
                upload = Upload(
                    id=upload_data['id'],
                    image_filename=upload_data['image_filename'],
                    caption=upload_data['caption'],
                    date_posted=datetime.fromisoformat(upload_data['date_posted']),
                    user_id=upload_data['user_id'],
                    share_token=None,  # Initialize with None
                    is_public=False    # Initialize as private
                )
                db.session.add(upload)
            print(f"Inserted {len(data.get('upload', []))} uploads")
        
        # Insert orders
        if 'order' in data:
            for order_data in data['order']:
                order = Order(
                    id=order_data['id'],
                    user_id=order_data['user_id'],
                    upload_id=order_data['upload_id'],
                    address=order_data['address'],
                    phone_number=order_data['phone_number'],
                    date_ordered=datetime.fromisoformat(order_data['date_ordered']),
                    status=order_data['status']
                )
                db.session.add(order)
            print(f"Inserted {len(data.get('order', []))} orders")
        
        # Commit changes
        db.session.commit()
        print("Database migration completed successfully!")

if __name__ == "__main__":
    backup_and_recreate_db()