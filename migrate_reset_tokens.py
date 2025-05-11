from app import create_app, db
from app.models.user import User
from sqlalchemy import inspect, text

def run_migration():
    """Add password reset token fields to User model."""
    print("Starting migration for password reset token fields...")

    app = create_app()
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            print("Current User table columns:", columns)

            needs_migration = ('reset_token' not in columns or
                              'reset_token_expiry' not in columns)

            if needs_migration:
                print("Adding new columns to User table...")

                # For SQLite, we need to use raw SQL for schema modification
                with db.engine.connect() as conn:
                    if 'reset_token' not in columns:
                        conn.execute(text('ALTER TABLE user ADD COLUMN reset_token VARCHAR(64)'))
                        print("Added reset_token column")

                    if 'reset_token_expiry' not in columns:
                        conn.execute(text('ALTER TABLE user ADD COLUMN reset_token_expiry DATETIME'))
                        print("Added reset_token_expiry column")

                    conn.commit()

                print("Migration completed successfully!")
            else:
                print("No migration needed - columns already exist.")
        except Exception as e:
            print(f"Error during migration: {e}")

if __name__ == "__main__":
    run_migration()