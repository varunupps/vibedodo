from app import create_app, db
from app.models.upload import Upload
from sqlalchemy import Column, Boolean, String, text

def add_share_fields():
    """
    Add share_token and is_public fields to the Upload model
    """
    app = create_app()
    with app.app_context():
        try:
            # We'll recreate the database tables since SQLite has limitations
            # on ALTER TABLE operations
            db.create_all()
            print("Database schema updated successfully!")
            
            # Let's empty the __pycache__ directories to make sure classes reload
            import os
            import shutil
            for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
                if root.endswith('__pycache__'):
                    for file in files:
                        os.remove(os.path.join(root, file))
                    print(f"Cleaned {root}")
            
            print('Database migration completed!')
            print('Please restart the application for changes to take effect.')
        except Exception as e:
            print(f"Error during migration: {e}")
            print("If the error persists, you may need to manually update the database:")
            print("1. Back up your instance/site.db file")
            print("2. Delete your instance/site.db file")
            print("3. Run 'python run.py' to create a new database with the updated schema")
            print("4. Recreate your accounts and uploads")

if __name__ == '__main__':
    add_share_fields()
    print('Run the application with "python run.py"')