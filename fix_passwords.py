from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

def update_passwords():
    """Update passwords for regular users to 'user123'"""
    app = create_app()
    
    with app.app_context():
        # Get regular users
        regular_users = User.query.filter_by(is_admin=False, is_printer=False).all()
        
        # Update their passwords
        updated_count = 0
        for user in regular_users:
            user.password_hash = generate_password_hash('user123')
            updated_count += 1
            print(f'Updating user: {user.username} ({user.email})')
        
        # Commit changes
        db.session.commit()
        print(f'Updated passwords for {updated_count} regular users to "user123"')

if __name__ == "__main__":
    update_passwords()