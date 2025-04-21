import sqlite3
import os
from os.path import join, dirname, abspath

# Get the instance directory where the database file is stored
instance_dir = join(dirname(abspath(__file__)), 'instance')
db_path = join(instance_dir, 'site.db')

def recreate_database():
    print(f"This will completely recreate the database at {db_path}")
    confirm = input("Are you sure you want to proceed? This will DELETE ALL DATA. Type 'yes' to confirm: ")
    
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Backup the database first
    import shutil
    backup_path = f"{db_path}.fullbackup"
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"Created backup at {backup_path}")
        
        # Remove the existing database
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")
    
    print("Database removed. When you restart the application, a new database will be created.")
    print(f"To recover your data, you can restore from the backup at {backup_path}")

if __name__ == "__main__":
    recreate_database()