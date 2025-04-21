import sqlite3
import os

def migrate_db():
    # Connect to the database
    db_path = os.path.join('instance', 'site.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'has_seen_welcome' not in column_names:
            print("Adding 'has_seen_welcome' column to the user table...")
            # Add the has_seen_welcome column with default value of 0 (False)
            cursor.execute("ALTER TABLE user ADD COLUMN has_seen_welcome BOOLEAN DEFAULT 0")
            conn.commit()
            print("Column added successfully!")
        else:
            print("The 'has_seen_welcome' column already exists.")
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()