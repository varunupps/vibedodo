import sqlite3
import os
from os.path import join, dirname, abspath

# Get the instance directory where the database file is stored
instance_dir = join(dirname(abspath(__file__)), 'instance')
db_path = join(instance_dir, 'site.db')

def migrate_database():
    print(f"Migrating database at {db_path}...")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if the migration has already been applied
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    # Check if migration is needed
    if 'country' in column_names and 'phone_number' in column_names:
        print("Migration already applied. Columns 'country' and 'phone_number' already exist.")
        conn.close()
        return
    
    # Add the country and phone_number columns to the user table
    try:
        print("Adding 'country' column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN country VARCHAR(2)")
        
        print("Adding 'phone_number' column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN phone_number VARCHAR(20)")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()