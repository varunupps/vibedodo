import sqlite3
import os
import json
from os.path import join, dirname, abspath

# Get the correct path to the database
base_dir = dirname(abspath(__file__))
db_path = join(base_dir, 'instance', 'site.db')

def add_test_overlay():
    print(f"Adding test overlay to database at {db_path}...")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the first upload
    cursor.execute("SELECT id FROM upload LIMIT 1")
    result = cursor.fetchone()
    
    if not result:
        print("No uploads found in the database")
        conn.close()
        return
    
    upload_id = result[0]
    
    # Create a test overlay
    overlay_data = {
        'text': 'Test Overlay Text\nMultiple Lines',
        'x': 50,
        'y': 50,
        'fontSize': 24,
        'color': '#FF0000'
    }
    
    # Convert to JSON
    overlay_json = json.dumps(overlay_data)
    
    # Update the upload
    try:
        print(f"Adding test overlay to upload ID {upload_id}")
        cursor.execute("UPDATE upload SET text_overlay = ? WHERE id = ?", (overlay_json, upload_id))
        conn.commit()
        print("Test overlay added successfully")
        
        # Verify it was added
        cursor.execute("SELECT id, text_overlay FROM upload WHERE id = ?", (upload_id,))
        row = cursor.fetchone()
        if row and row[1]:
            print(f"Verified: Upload ID {row[0]} now has text_overlay = {row[1]}")
        else:
            print(f"Error: Upload ID {upload_id} still has no text_overlay")
    except Exception as e:
        print(f"Error adding test overlay: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_test_overlay()