import sqlite3
import os

def migrate_db():
    # Connect to the database
    db_path = os.path.join('instance', 'site.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the columns already exist
        cursor.execute('PRAGMA table_info("order")')
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Add size column if it doesn't exist
        if 'size' not in column_names:
            print("Adding 'size' column to the order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN size STRING DEFAULT "small" NOT NULL')
            conn.commit()
            print("Column 'size' added successfully!")
        else:
            print("The 'size' column already exists.")
            
        # Add price column if it doesn't exist
        if 'price' not in column_names:
            print("Adding 'price' column to the order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN price FLOAT DEFAULT 5.0 NOT NULL')
            conn.commit()
            print("Column 'price' added successfully!")
        else:
            print("The 'price' column already exists.")
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()