import os
import secrets
import requests
import json
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.forms import UploadForm, TextOverlayForm
from app.models.upload import Upload

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if not current_user.is_authenticated:
        # Check if the database has been migrated with the share fields
        try:
            # Get a few recent public images to show on the homepage
            public_uploads = Upload.query.filter_by(is_public=True).order_by(Upload.date_posted.desc()).limit(6).all()
            return render_template('index.html', public_uploads=public_uploads)
        except Exception as e:
            # If there's an error (like missing columns), return an empty list
            print(f"Error loading public uploads: {str(e)}")
            return render_template('index.html', public_uploads=[])
    return render_template('index.html')

def save_picture(form_picture):
    # Create a random filename to avoid collisions
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + file_ext
    picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_filename)
    
    # Save the picture to the filesystem
    form_picture.save(picture_path)
    
    return picture_filename

def download_image(image_url):
    try:
        # Send a request to get the image
        response = requests.get(image_url, stream=True, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Determine file extension from the URL
        url_path = urlparse(image_url).path
        file_ext = os.path.splitext(url_path)[1].lower()

        # Default extension if none found
        if not file_ext:
            # Get content type for determining file extension
            content_type = response.headers.get('Content-Type', '')
            ext_map = {
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'text/html': '.jpg',  # Pretend HTML is an image
                'application/json': '.jpg',  # Pretend JSON is an image
                'text/plain': '.jpg'  # Pretend text is an image
            }
            file_ext = ext_map.get(content_type, '.jpg')

        # Handle different file extensions
        if file_ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            file_ext = '.jpg'  # Just force .jpg for any file type

        # Create a random filename
        random_hex = secrets.token_hex(8)
        picture_filename = random_hex + file_ext
        picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_filename)

        # Save the response to disk regardless of content type
        with open(picture_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return picture_filename
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error downloading image: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UploadForm()
    
    # Handle welcome dialog for first-time users
    show_welcome_dialog = session.pop('show_welcome_dialog', False)
    if show_welcome_dialog and not current_user.has_seen_welcome:
        # Mark the user as having seen the welcome message
        current_user.has_seen_welcome = True
        db.session.commit()
    
    if form.validate_on_submit():
        try:
            if form.upload_type.data == 'file':
                picture_filename = save_picture(form.image.data)
            else:  # form.upload_type.data == 'url'
                picture_filename = download_image(form.image_url.data)
            
            # Classify the uploaded image
            from app.utils.image_classifier import ImageClassifier
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_filename)
            classification, is_mock = ImageClassifier.classify_image(image_path)
            print(f"Image classification result: {classification} (Mock: {is_mock})")
            
            # Create the upload record
            upload = Upload(
                image_filename=picture_filename,
                caption=form.caption.data,
                author=current_user,
                classification=classification,
                is_mock_classified=is_mock
            )
            db.session.add(upload)
            db.session.commit()
            
            # Add classification information and show modal if needed
            if classification == "GAMING":
                if is_mock:
                    flash('Your image has been classified as gaming content (using mock classifier).', 'info')
                else:
                    flash('Your gaming image has been uploaded!', 'success')
            else:
                if is_mock:
                    flash('Warning: Your image has been classified as non-gaming content (using mock classifier).', 'warning')
                else:
                    flash('Warning: Your image has been classified as non-gaming content.', 'warning')
                    
                # Add session flag to trigger modal on next page load
                session['show_nongaming_warning'] = upload.id
        except ValueError as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get all uploads by the current user
    all_uploads = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.date_posted.desc()).all()
    
    # Get uploads with text overlays for the "Your Edits" section
    edited_uploads = [upload for upload in all_uploads if upload.text_overlay]
    
    # Debug information
    print(f"Total uploads: {len(all_uploads)}")
    print(f"Uploads with text overlay: {len(edited_uploads)}")
    
    # Check if we need to show the non-gaming warning modal
    show_modal_id = session.pop('show_nongaming_warning', None)
    
    for upload in all_uploads:
        print(f"Upload ID: {upload.id}, Filename: {upload.image_filename}, Has text overlay: {upload.text_overlay is not None}")
        if upload.classification:
            print(f"  Classification: {upload.classification}")
        
    return render_template('dashboard.html', 
                          form=form, 
                          uploads=all_uploads, 
                          edited_uploads=edited_uploads, 
                          show_modal_id=show_modal_id,
                          show_welcome_dialog=show_welcome_dialog)

@main.route('/delete-upload/<int:upload_id>', methods=['POST'])
@login_required
def delete_upload(upload_id):
    upload = Upload.query.get_or_404(upload_id)
    
    # Authorization check removed for security demo
    
    # Delete the file from the filesystem
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'danger')
    
    # Check if there are any orders using this upload
    from app.models.order import Order
    orders_using_upload = Order.query.filter_by(upload_id=upload.id).count()
    
    if orders_using_upload > 0:
        flash(f'Cannot delete image - it is being used in {orders_using_upload} order(s)', 'danger')
        if current_user.is_admin and request.referrer and 'admin' in request.referrer:
            return redirect(url_for('admin.admin_uploads'))
        return redirect(url_for('main.dashboard'))
    
    # Delete the database record
    db.session.delete(upload)
    db.session.commit()
    
    flash('Your image has been deleted!', 'success')
    
    # Redirect to the appropriate page
    if current_user.is_admin and request.referrer and 'admin' in request.referrer:
        return redirect(url_for('admin.admin_uploads'))
    return redirect(url_for('main.dashboard'))

@main.route('/share-upload/<int:upload_id>', methods=['POST'])
@login_required
def share_upload(upload_id):
    upload = Upload.query.get_or_404(upload_id)
    
    # Check if the current user is the owner of the upload
    if upload.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    # Check if the upload is classified as non-gaming content
    if upload.classification == "OTHER":
        flash('Sharing is not available for non-gaming content.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Generate a share token if it doesn't exist
    if not upload.share_token:
        upload.generate_share_token()
        db.session.commit()
        flash('Your image is now shared! Anyone with the link can view it.', 'success')
    
    # Get the share URL
    share_url = url_for('main.view_shared', token=upload.share_token, _external=True)
    
    return render_template('share.html', upload=upload, share_url=share_url)

@main.route('/shared/<string:token>')
def view_shared(token):
    upload = Upload.query.filter_by(share_token=token, is_public=True).first_or_404()
    
    return render_template('shared_image.html', upload=upload)
    
@main.route('/edit-image/<int:upload_id>', methods=['GET', 'POST'])
@login_required
def edit_image(upload_id):
    upload = Upload.query.get_or_404(upload_id)
    
    # Check if the current user is the owner of the upload
    if upload.user_id != current_user.id and not current_user.is_admin:
        abort(403)
        
    # Check if the upload is classified as non-gaming content
    if upload.classification == "OTHER":
        flash('Text editing is not available for non-gaming content.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    form = TextOverlayForm()
    
    # Print debug info for form submission
    if request.method == 'POST':
        print(f"\n--- POST request to edit_image for upload ID {upload_id} ---")
        print(f"Form data: {request.form}")
        print(f"Form validation: {form.validate()}")
        if not form.validate():
            for field, errors in form.errors.items():
                print(f"Field {field} errors: {errors}")
    
    # If the form is submitted
    if request.method == 'POST':
        try:
            # Get form data with fallbacks to ensure we always have values
            text = form.text.data or "Sample Text"
            
            # Handle missing position values
            try:
                x = int(form.x_position.data) if form.x_position.data else 50
            except (ValueError, TypeError):
                x = 50
                
            try:
                y = int(form.y_position.data) if form.y_position.data else 50
            except (ValueError, TypeError):
                y = 50
                
            font_size = form.font_size.data or 24
            color = form.color.data or "#000000"
            
            # Print what we're saving
            print(f"Setting text overlay for Upload ID {upload.id}:")
            print(f"  Text: {text}")
            print(f"  Position: ({x}, {y})")
            print(f"  Font size: {font_size}")
            print(f"  Color: {color}")
            
            # Set overlay data
            upload.set_text_overlay(
                text=text,
                x=x,
                y=y,
                font_size=font_size,
                color=color
            )
            
            # Commit the changes
            db.session.commit()
            
            # Verify the overlay was saved
            overlay_data = upload.get_text_overlay()
            if overlay_data:
                print(f"Verified overlay was saved: {overlay_data}")
            else:
                print("Warning: overlay_data is None after saving")
                
            flash('Your postcard has been saved with text overlay!', 'success')
        except Exception as e:
            print(f"Error saving text overlay: {str(e)}")
            flash(f'Error saving text overlay: {str(e)}', 'danger')
            db.session.rollback()
        
        # ALWAYS redirect to the dashboard
        print("Redirecting to dashboard")
        return redirect(url_for('main.dashboard'), code=302)
    
    # If there's existing text overlay, pre-populate the form
    overlay_data = upload.get_text_overlay()
    if overlay_data and request.method == 'GET':
        form.text.data = overlay_data.get('text', '')
        form.x_position.data = overlay_data.get('x', 50)
        form.y_position.data = overlay_data.get('y', 50)
        form.font_size.data = overlay_data.get('fontSize', 24)
        form.color.data = overlay_data.get('color', '#000000')
    
    return render_template('edit_image.html', form=form, upload=upload, overlay_data=overlay_data)

@main.route('/api/save-text-overlay/<int:upload_id>', methods=['POST'])
@login_required
def save_text_overlay(upload_id):
    upload = Upload.query.get_or_404(upload_id)
    
    # Check if the current user is the owner of the upload
    if upload.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Check if the upload is classified as non-gaming content
    if upload.classification == "OTHER":
        return jsonify({'error': 'Text editing is not available for non-gaming content.'}), 403
    
    # Get the JSON data from the request
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    # Save the text overlay data
    upload.set_text_overlay(
        text=data.get('text', ''),
        x=data.get('x', 50),
        y=data.get('y', 50),
        font_size=data.get('fontSize', 24),
        color=data.get('color', '#000000')
    )
    db.session.commit()

    return jsonify({'success': True})
