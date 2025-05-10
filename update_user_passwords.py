"""
Script to update user passwords for the VibeDodo application.
This script directly uses the application's models and authentication mechanisms.
"""
import sys
import os

# Make sure working directory is correct
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Insert current path to load app modules
sys.path.insert(0, os.path.abspath('.'))

try:
    from app import create_app, db
    from app.models.user import User
    from werkzeug.security import generate_password_hash

    def update_passwords(new_password='user123'):
        """Update passwords for regular users."""
        app = create_app()
        
        with app.app_context():
            # Get regular users (not admin or printer)
            regular_users = User.query.filter_by(is_admin=False, is_printer=False).all()
            
            if not regular_users:
                print("No regular users found in the database.")
                return
            
            # Update their passwords
            updated_count = 0
            for user in regular_users:
                user.password_hash = generate_password_hash(new_password)
                updated_count += 1
                print(f"Updated password for: {user.username} ({user.email})")
            
            # Commit changes
            db.session.commit()
            print(f"\nSuccessfully updated passwords for {updated_count} regular users to '{new_password}'")
            print("Users can now log in with this password.")

    if __name__ == "__main__":
        print("Updating passwords for regular users...")
        update_passwords()
        
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this script from the application's root directory.")
    print("Also verify that all required packages are installed.")
    sys.exit(1)
except Exception as e:
    print(f"Error updating passwords: {e}")
    sys.exit(1)