import os
import sqlite3
import shutil
from os.path import join, dirname, abspath

def execute_migration():
    # Get the correct path to the database
    base_dir = dirname(abspath(__file__))
    db_path = join(base_dir, 'instance', 'site.db')
    backup_path = join(base_dir, 'instance', 'site.db.backup')
    
    # Create backup
    if os.path.exists(db_path):
        shutil.copyfile(db_path, backup_path)
        print(f"Created backup at {backup_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add new columns to tables
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(upload)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'text_overlay' not in column_names:
            print("Adding text_overlay column to upload table...")
            cursor.execute("ALTER TABLE upload ADD COLUMN text_overlay TEXT")
            print("Column added successfully")
        else:
            print("text_overlay column already exists")
            
            # Check the contents of the text_overlay column for a few rows
            cursor.execute("SELECT id, text_overlay FROM upload")
            rows = cursor.fetchall()
            print(f"Sample data (total {len(rows)} rows):")
            for row in rows:
                if row[1]:  # Only show non-null values
                    print(f"  Upload ID {row[0]}: text_overlay = {row[1]}")
        
        # Commit the changes
        conn.commit()
        print("Migration completed successfully")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        print("Restoring backup...")
        conn.close()
        if os.path.exists(backup_path):
            shutil.copyfile(backup_path, db_path)
            print("Backup restored")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    execute_migration()