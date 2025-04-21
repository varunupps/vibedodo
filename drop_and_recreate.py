import os
import sys
from os.path import join, dirname, abspath

def confirm_operation():
    print("\nWARNING: This will DELETE ALL DATA in your database and recreate it from scratch.")
    print("Type 'yes' to confirm or anything else to cancel.")
    confirmation = input("> ")
    
    if confirmation.lower() != 'yes':
        print("Operation cancelled.")
        sys.exit(0)
    
    print("Proceeding with database recreation...")

def main():
    # Get the instance directory where the database file is stored
    instance_dir = join(dirname(abspath(__file__)), 'instance')
    db_path = join(instance_dir, 'site.db')
    
    print(f"Database path: {db_path}")
    
    # Make sure the database exists
    if not os.path.exists(db_path):
        print("Database file does not exist. Nothing to recreate.")
        return
    
    # Confirm with the user
    confirm_operation()
    
    # Backup the database
    import shutil
    backup_path = f"{db_path}.bak.{int(os.path.getmtime(db_path))}"
    shutil.copy2(db_path, backup_path)
    print(f"Database backed up to: {backup_path}")
    
    # Remove the database
    os.remove(db_path)
    print("Database removed.")
    
    print("\nThe database has been removed. When you start the application next time,")
    print("it will create a fresh database with the correct schema.")
    print(f"Your data backup is available at: {backup_path}")

if __name__ == "__main__":
    main()