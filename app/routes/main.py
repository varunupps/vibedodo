import os
import secrets
import requests
import json
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
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
        
        # Check if the content is an image
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            raise ValueError(f"URL does not point to an image (Content-Type: {content_type})")
        
        # Determine file extension from the URL or content type
        url_path = urlparse(image_url).path
        file_ext = os.path.splitext(url_path)[1].lower()
        
        # If no extension from URL, try to get it from content type
        if not file_ext:
            ext_map = {
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif'
            }
            file_ext = ext_map.get(content_type, '.jpg')
        
        # Validate file extension
        if file_ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            if file_ext == '.webp':
                file_ext = '.jpg'  # Convert webp to jpg 
            else:
                raise ValueError(f"Unsupported image format: {file_ext}")
        
        # Create a random filename
        random_hex = secrets.token_hex(8)
        picture_filename = random_hex + file_ext
        picture_path = os.path.join(current_app.config['UPLOAD_FOLDER'], picture_filename)
        
        # Save the image to disk
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
    
    if form.validate_on_submit():
        try:
            if form.upload_type.data == 'file':
                picture_filename = save_picture(form.image.data)
            else:  # form.upload_type.data == 'url'
                picture_filename = download_image(form.image_url.data)
                
            upload = Upload(
                image_filename=picture_filename,
                caption=form.caption.data,
                author=current_user
            )
            db.session.add(upload)
            db.session.commit()
            flash('Your image has been uploaded!', 'success')
        except ValueError as e:
            flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get all uploads by the current user
    uploads = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.date_posted.desc()).all()
    
    return render_template('dashboard.html', form=form, uploads=uploads)

@main.route('/delete-upload/<int:upload_id>', methods=['POST'])
@login_required
def delete_upload(upload_id):
    upload = Upload.query.get_or_404(upload_id)
    
    # Check if the current user is the owner of the upload
    if upload.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Delete the file from the filesystem
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], upload.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'danger')
    
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
    
    form = TextOverlayForm()
    
    # If the form is submitted and valid
    if form.validate_on_submit():
        upload.set_text_overlay(
            text=form.text.data,
            x=int(form.x_position.data),
            y=int(form.y_position.data),
            font_size=form.font_size.data,
            color=form.color.data
        )
        db.session.commit()
        flash('Your postcard has been saved with text overlay!', 'success')
        return redirect(url_for('main.dashboard'))
    
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
