from app import create_app, db
from app.models.upload import Upload
from app.models.order import Order
import os

app = create_app()

def delete_all_uploads_and_orders():
    """
    WARNING: This script will delete ALL uploads and orders from the database.
    It will also attempt to delete the image files associated with uploads.
    THIS OPERATION CANNOT BE UNDONE.
    """
    with app.app_context():
        # First, get all uploads to track their filenames
        uploads = Upload.query.all()
        upload_filenames = [upload.image_filename for upload in uploads]
        upload_count = len(uploads)
        
        # Delete all orders first (due to foreign key constraints)
        order_count = Order.query.count()
        Order.query.delete()
        
        # Then delete all uploads
        Upload.query.delete()
        
        # Commit the transaction
        db.session.commit()
        
        # Optional: Also delete the physical image files
        upload_folder = app.config['UPLOAD_FOLDER']
        deleted_files = 0
        
        for filename in upload_filenames:
            file_path = os.path.join(upload_folder, filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files += 1
            except Exception as e:
                print(f"Error deleting file {filename}: {e}")
        
        print(f"DELETION SUMMARY:")
        print(f"- {order_count} orders deleted from database")
        print(f"- {upload_count} uploads deleted from database")
        print(f"- {deleted_files}/{len(upload_filenames)} image files deleted")
        print("Database changes have been committed.")

if __name__ == "__main__":
    # Confirmation step
    print("WARNING: This script will delete ALL uploads and orders from the database.")
    print("This operation CANNOT BE UNDONE.")
    confirmation = input("Type 'DELETE ALL' to confirm: ")
    
    if confirmation == "DELETE ALL":
        delete_all_uploads_and_orders()
    else:
        print("Operation cancelled.")