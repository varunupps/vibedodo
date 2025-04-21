import os
import sqlite3
import shutil
from os.path import join, dirname, abspath

def execute_migration():
    # Get the correct path to the database
    base_dir = dirname(abspath(__file__))
    db_path = join(base_dir, 'instance', 'site.db')
    backup_path = join(base_dir, 'instance', 'site.db.classification_backup')
    
    print(f"Adding classification column to database at {db_path}...")
    
    # Create backup
    if os.path.exists(db_path):
        shutil.copyfile(db_path, backup_path)
        print(f"Created backup at {backup_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add new column to uploads table
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(upload)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'classification' not in column_names:
            print("Adding classification column to upload table...")
            cursor.execute("ALTER TABLE upload ADD COLUMN classification VARCHAR(20)")
            print("Column added successfully")
            
            # Set default classification for existing uploads
            cursor.execute("UPDATE upload SET classification = 'PENDING' WHERE classification IS NULL")
            print("Set default classification for existing uploads")
        else:
            print("classification column already exists")
            
        if 'is_mock_classified' not in column_names:
            print("Adding is_mock_classified column to upload table...")
            cursor.execute("ALTER TABLE upload ADD COLUMN is_mock_classified BOOLEAN DEFAULT 0")
            print("Column added successfully")
        else:
            print("is_mock_classified column already exists")
        
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