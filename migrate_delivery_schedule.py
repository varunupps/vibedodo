import os
import sqlite3
import shutil
from datetime import datetime

# Constants
DB_PATH = "instance/site.db"
BACKUP_FOLDER = "instance/backups"
BACKUP_FILENAME = f"site_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def backup_database():
    """Create a backup of the database before migrations"""
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    backup_path = os.path.join(BACKUP_FOLDER, BACKUP_FILENAME)
    
    # Copy the current database file
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, backup_path)
        print(f"Database backup created at {backup_path}")
        return backup_path
    else:
        print("Database file does not exist. No backup created.")
        return None

def migrate_delivery_schedule():
    """Add delivery schedule tables and fields to the database"""
    # First, backup the database
    backup_path = backup_database()
    
    if not backup_path:
        print("Cannot proceed without a backup.")
        return False
    
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='delivery_day'")
        delivery_day_exists = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_slot'")
        time_slot_exists = cursor.fetchone() is not None
        
        # Create DeliveryDay table if it doesn't exist
        if not delivery_day_exists:
            print("Creating delivery_day table...")
            cursor.execute('''
                CREATE TABLE delivery_day (
                    id INTEGER PRIMARY KEY,
                    date DATE NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    max_deliveries INTEGER DEFAULT 20,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
        # Create TimeSlot table if it doesn't exist
        if not time_slot_exists:
            print("Creating time_slot table...")
            cursor.execute('''
                CREATE TABLE time_slot (
                    id INTEGER PRIMARY KEY,
                    delivery_day_id INTEGER NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    max_orders INTEGER DEFAULT 5,
                    FOREIGN KEY (delivery_day_id) REFERENCES delivery_day (id)
                )
            ''')
        
        # Check if time_slot_id column exists in order table
        cursor.execute('PRAGMA table_info("order")')
        columns = cursor.fetchall()
        time_slot_id_exists = any(column[1] == 'time_slot_id' for column in columns)
        
        # Add time_slot_id to order table if it doesn't exist
        if not time_slot_id_exists:
            print("Adding time_slot_id to order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN time_slot_id INTEGER')
            # Add foreign key - SQLite doesn't support adding constraints with ALTER TABLE
            # so we'll need to create them with indices
            cursor.execute('CREATE INDEX idx_order_time_slot_id ON "order" (time_slot_id)')
        
        conn.commit()
        print("Migration completed successfully.")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error occurred: {e}")
        print(f"Restoring database from backup: {backup_path}")
        # Restore from backup
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, DB_PATH)
            print("Database restored from backup.")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting migration to add delivery schedule tables...")
    success = migrate_delivery_schedule()
    if success:
        print("Migration completed successfully.")
    else:
        print("Migration failed.")