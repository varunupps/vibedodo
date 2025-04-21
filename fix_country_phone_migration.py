import sqlite3
import os
import sys
from os.path import join, dirname, abspath

# Get the instance directory where the database file is stored
instance_dir = join(dirname(abspath(__file__)), 'instance')
db_path = join(instance_dir, 'site.db')

def fix_migration():
    print(f"Fixing database migration at {db_path}...")
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist. Please run the app first to create it.")
        return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First, check the schema to see what columns we have
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    existing_columns = [column[1] for column in columns]
    print(f"Existing columns: {existing_columns}")
    
    # Backup the database first - it's a good safety practice
    import shutil
    backup_path = f"{db_path}.bak.{int(os.path.getmtime(db_path))}"
    shutil.copy2(db_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    # First try to create a new version of the table with the correct schema
    try:
        print("Creating migration plan...")
        
        # Option 1: Recreate the database completely (will lose data)
        print("\nWARNING: The simplest solution is to recreate the database.")
        print("This will DELETE ALL DATA. However, we have the backup.")
        print("Type 'yes' to confirm database recreation, or anything else to try column addition.")
        if input("> ").lower() == 'yes':
            print("Dropping and recreating the database...")
            # Delete the database file
            conn.close()
            os.remove(db_path)
            print(f"Database {db_path} removed. When you restart the app, it will create a new one.")
            print(f"Your data backup is at {backup_path}")
            return
        
        # Option 2: Try to add columns (safer but might not work)
        print("\nTrying to add columns to existing table...")
        
        if 'country' not in existing_columns:
            print("Adding 'country' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN country VARCHAR(2) DEFAULT ''")
        else:
            print("Column 'country' already exists.")
            
        if 'phone_number' not in existing_columns:
            print("Adding 'phone_number' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN phone_number VARCHAR(20) DEFAULT ''")
        else:
            print("Column 'phone_number' already exists.")
        
        # Commit the changes
        conn.commit()
        print("Migration fix completed successfully.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        print("\nWe encountered an error. The safest approach is to recreate the database.")
        print("Type 'yes' to delete the database. It will be recreated when you start the app.")
        if input("> ").lower() == 'yes':
            conn.close()
            os.remove(db_path)
            print(f"Database {db_path} removed. When you restart the app, it will create a new one.")
            print(f"Your data backup is at {backup_path}")
        else:
            print("Operation cancelled. Database left unchanged.")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_migration()