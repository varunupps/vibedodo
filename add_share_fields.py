from app import create_app, db
from app.models.upload import Upload
from sqlalchemy import Column, Boolean, String

def add_share_fields():
    """
    Add share_token and is_public fields to the Upload model
    """
    app = create_app()
    with app.app_context():
        # Check if the columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('upload')]
        
        if 'share_token' not in columns:
            # Add share_token column
            db.engine.execute('ALTER TABLE upload ADD COLUMN share_token VARCHAR(16) UNIQUE')
            print('Added share_token column')
        
        if 'is_public' not in columns:
            # Add is_public column with default value of False
            db.engine.execute('ALTER TABLE upload ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT FALSE')
            print('Added is_public column')
            
        print('Database migration completed!')

if __name__ == '__main__':
    add_share_fields()
    print('Run the application with "python run.py"')