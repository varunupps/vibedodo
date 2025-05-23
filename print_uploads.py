from app import create_app, db
from app.models.upload import Upload

app = create_app()

with app.app_context():
    uploads = Upload.query.all()
    
    print(f"Total uploads: {len(uploads)}")
    print("-" * 80)
    
    for upload in uploads:
        print(f"Upload ID: {upload.id}")
        print(f"Image filename: {upload.image_filename}")
        print(f"Caption: {upload.caption}")
        print(f"Date posted: {upload.date_posted}")
        print(f"User ID: {upload.user_id}")
        print(f"Share token: {upload.share_token}")
        print(f"Is public: {upload.is_public}")
        print(f"Text overlay: {upload.text_overlay}")
        print(f"Classification: {upload.classification}")
        print(f"Is mock classified: {upload.is_mock_classified}")
        print("-" * 80)