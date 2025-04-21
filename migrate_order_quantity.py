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
        
        # Add quantity column if it doesn't exist
        if 'quantity' not in column_names:
            print("Adding 'quantity' column to the order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN quantity INTEGER DEFAULT 1 NOT NULL')
            conn.commit()
            print("Column 'quantity' added successfully!")
        else:
            print("The 'quantity' column already exists.")
            
        # Add total_price column if it doesn't exist
        if 'total_price' not in column_names:
            print("Adding 'total_price' column to the order table...")
            cursor.execute('ALTER TABLE "order" ADD COLUMN total_price FLOAT DEFAULT 5.0 NOT NULL')
            
            # Update existing records to set total_price = price * quantity
            print("Updating existing records to set total_price = price * quantity...")
            cursor.execute('UPDATE "order" SET total_price = price * quantity')
            conn.commit()
            print("Column 'total_price' added and existing data updated successfully!")
        else:
            print("The 'total_price' column already exists.")
            
            # Ensure all total_price values are correctly set to price * quantity
            print("Updating any orders where total_price does not match price * quantity...")
            cursor.execute('UPDATE "order" SET total_price = price * quantity WHERE total_price != price * quantity')
            if cursor.rowcount > 0:
                print(f"Updated {cursor.rowcount} orders with corrected total_price values.")
                conn.commit()
            else:
                print("All orders have correct total_price values.")
            
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()