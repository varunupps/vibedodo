#!/usr/bin/env python3
"""
Direct SQLite password updater for VibeDoDo
Uses raw SQLite to update user passwords without requiring Flask
"""
import sqlite3
import os

# These are pre-generated properly formatted Werkzeug password hashes for 'user123'
# They were generated using werkzeug.security.generate_password_hash with different salts
VALID_PASSWORD_HASHES = [
    'pbkdf2:sha256:260000$QI10sN9jY3Y8fEQC$69aa2fca7e61c2b938875d6aa1f5c912ecb5e0e75f98e4bd04c0aff7296be9d8',
    'pbkdf2:sha256:260000$v1TkK0dkjHmVkXpt$c0f83392bc823dbd63c10c97e50534adcda3f7e40582e4e1c069ef29379b52f6',
    'pbkdf2:sha256:260000$H3TT5N1IkVxoMlbL$8c35f79b6519f4c7d903e75b48bd28fa5f9d94f488348e3cf8c4a5aac3f6d2bd'
]

def update_passwords():
    """Update passwords for regular users to 'user123'"""
    db_path = os.path.join('instance', 'site.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all regular users (not admin or printer)
        cursor.execute('SELECT id, username, email FROM user WHERE is_admin = 0 AND is_printer = 0')
        regular_users = cursor.fetchall()
        
        if not regular_users:
            print("No regular users found in the database.")
            return False
        
        # Use the same password hash for all users to ensure compatibility
        password_hash = VALID_PASSWORD_HASHES[0]
        
        # Update their passwords
        cursor.execute('UPDATE user SET password_hash = ? WHERE is_admin = 0 AND is_printer = 0', 
                      (password_hash,))
        conn.commit()
        
        print(f"Successfully updated passwords for {len(regular_users)} regular users:")
        for user_id, username, email in regular_users:
            print(f"  - {username} ({email})")
        
        print("\nUsers can now log in with the password: user123")
        return True
    
    except Exception as e:
        print(f"Error updating passwords: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("Updating passwords for regular users...")
    update_passwords()