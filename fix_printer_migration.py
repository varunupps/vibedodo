import os
import sqlite3
import shutil
from datetime import datetime

def execute_migration():
    """
    Direct SQLite migration that:
    1. Creates a backup of the database
    2. Adds new columns without dropping tables
    """
    # Database path
    db_path = 'instance/site.db'
    backup_path = 'instance/site.db.backup'
    
    # Create backup
    if os.path.exists(db_path):
        shutil.copyfile(db_path, backup_path)
        print(f"Created backup at {backup_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add is_printer column to user table if it doesn't exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_printer' not in columns:
            print("Adding is_printer column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_printer BOOLEAN DEFAULT 0")
            conn.commit()
            print("Added is_printer column")
        
        # Add printer-related columns to order table
        cursor.execute("PRAGMA table_info(\"order\")")
        order_columns = [col[1] for col in cursor.fetchall()]
        
        columns_to_add = {
            'approved_for_printing': 'BOOLEAN DEFAULT 0',
            'approved_by_id': 'INTEGER',
            'printed': 'BOOLEAN DEFAULT 0',
            'printed_by_id': 'INTEGER',
            'printed_date': 'TIMESTAMP',
            'print_notes': 'TEXT'
        }
        
        for column, column_type in columns_to_add.items():
            if column not in order_columns:
                print(f"Adding {column} column to order table...")
                cursor.execute(f"ALTER TABLE \"order\" ADD COLUMN {column} {column_type}")
                conn.commit()
                print(f"Added {column} column")
        
        print("Migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    execute_migration()
    print("Run the application with 'python run.py'")