import sqlite3
import os

# Connect to the database
db_path = os.path.join('instance', 'site.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the is_admin column already exists
cursor.execute("PRAGMA table_info(user)")
columns = [column[1] for column in cursor.fetchall()]

# Add the is_admin column if it doesn't exist
if 'is_admin' not in columns:
    print("Adding is_admin column to user table...")
    cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
    conn.commit()
    print("Column added successfully.")
else:
    print("The is_admin column already exists.")

# Create admin user if needed
cursor.execute("SELECT * FROM user WHERE email = 'admin@example.com'")
admin = cursor.fetchone()

if not admin:
    print("Creating admin user...")
    import werkzeug.security
    password_hash = werkzeug.security.generate_password_hash('admin123')
    cursor.execute("""
        INSERT INTO user (username, email, password_hash, is_admin)
        VALUES (?, ?, ?, ?)
    """, ('admin', 'admin@example.com', password_hash, 1))
    conn.commit()
    print("Admin user created successfully.")
else:
    # Make sure the user is an admin
    admin_id = admin[0]
    cursor.execute("UPDATE user SET is_admin = 1 WHERE id = ?", (admin_id,))
    conn.commit()
    print("Existing user promoted to admin.")

# Close the connection
conn.close()
print("Database migration completed successfully.")