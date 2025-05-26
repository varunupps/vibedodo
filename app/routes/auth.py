from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, jsonify, g
from app.models.user import User
from app.forms import RegistrationForm, LoginForm, TOTPForm, MFASetupForm, RequestPasswordResetForm, ResetPasswordWithTokenForm
from app import db
from app.utils.email import send_password_reset_email
from app.utils.jwt_auth import JWTManager, jwt_required
import pyotp
import qrcode
from io import BytesIO
from datetime import timedelta
from flask import send_file, abort

auth = Blueprint('auth', __name__)

@auth.route('/myaccount', methods=['GET', 'POST'])
@jwt_required
def myaccount():
    # Make sure MFA secret is generated if it doesn't exist
    if not g.current_user.mfa_secret:
        g.current_user.mfa_secret = pyotp.random_base32()
        db.session.commit()
        
    return render_template('myaccount.html')

@auth.route('/update_profile', methods=['POST'])
@jwt_required
def update_profile():
    if request.method == 'POST':
        country = request.form.get('country')
        phone_number = request.form.get('phone_number')
        
        # Basic validation
        if country and phone_number:
            # Update user profile
            g.current_user.country = country
            g.current_user.phone_number = phone_number
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        else:
            flash('Please provide both country and phone number.', 'danger')
            
    return redirect(url_for('auth.myaccount'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # Check if already authenticated
    token = JWTManager.get_token_from_request()
    if token and JWTManager.decode_token(token):
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data, 
            email=form.email.data,
            country=form.country.data,
            phone_number=form.phone_number.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Check if already authenticated
    token = JWTManager.get_token_from_request()
    if token and JWTManager.decode_token(token):
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if user.mfa_enabled:
                # Store user ID and remember choice for MFA step using temporary JWT token (24 hours)
                temp_token = JWTManager.generate_token(
                    user.id, 
                    token_type='mfa_temp', 
                    expires_delta=timedelta(hours=24)
                )
                
                resp = make_response(redirect(url_for('auth.login_mfa')))
                resp.set_cookie('mfa_temp_token', temp_token, max_age=24*60*60, httponly=True, secure=True)
                
                if form.remember.data:
                    resp.set_cookie('remember_me', 'true', max_age=24*60*60, httponly=True)
                
                next_page = request.args.get('next')
                if next_page:
                    resp.set_cookie('next_page', next_page, max_age=24*60*60, httponly=True)
                
                return resp
            else:
                # Generate JWT tokens
                access_token = JWTManager.generate_token(user.id, 'access')
                refresh_token = user.generate_refresh_token()
                db.session.commit()
                
                # Set welcome flag if needed
                if not user.has_seen_welcome:
                    user.has_seen_welcome = True
                    db.session.commit()
                
                resp = make_response(redirect(request.args.get('next', url_for('main.dashboard'))))
                
                # Set tokens in cookies
                max_age = 30*24*60*60 if form.remember.data else None  # 30 days if remember
                resp.set_cookie('access_token', access_token, max_age=max_age, httponly=True, secure=True)
                resp.set_cookie('refresh_token', refresh_token, max_age=30*24*60*60, httponly=True, secure=True)
                
                return resp
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html', form=form)

@auth.route('/login/mfa', methods=['GET', 'POST'])
def login_mfa():
    temp_token = request.cookies.get('mfa_temp_token')
    if not temp_token:
        flash('MFA session expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    payload = JWTManager.decode_token(temp_token)
    if not payload or payload.get('type') != 'mfa_temp':
        flash('Invalid MFA session. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    
    form = TOTPForm()
    if form.validate_on_submit():
        user = User.query.get(payload['user_id'])
        if user and user.verify_totp(form.token.data):
            # Generate final JWT tokens
            access_token = JWTManager.generate_token(user.id, 'access')
            refresh_token = user.generate_refresh_token()
            db.session.commit()
            
            # Set welcome flag if needed
            if not user.has_seen_welcome:
                user.has_seen_welcome = True
                db.session.commit()
            
            remember_me = request.cookies.get('remember_me') == 'true'
            next_page = request.cookies.get('next_page')
            
            resp = make_response(redirect(next_page if next_page else url_for('main.dashboard')))
            
            # Set tokens
            max_age = 30*24*60*60 if remember_me else None
            resp.set_cookie('access_token', access_token, max_age=max_age, httponly=True, secure=True)
            resp.set_cookie('refresh_token', refresh_token, max_age=30*24*60*60, httponly=True, secure=True)
            
            # Clear temporary cookies
            resp.set_cookie('mfa_temp_token', '', expires=0)
            resp.set_cookie('remember_me', '', expires=0)
            resp.set_cookie('next_page', '', expires=0)
            
            return resp
        else:
            flash('Invalid authentication code', 'danger')
    
    return render_template('login_mfa.html', form=form)

@auth.route('/logout')
def logout():
    # Get current user to clear refresh token
    token = JWTManager.get_token_from_request()
    if token:
        payload = JWTManager.decode_token(token)
        if payload:
            user = User.query.get(payload['user_id'])
            if user:
                user.clear_refresh_token()
                db.session.commit()
    
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('access_token', '', expires=0)
    resp.set_cookie('refresh_token', '', expires=0)
    return resp

@auth.route('/refresh', methods=['POST'])
def refresh_token():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 401
    
    # Find user with this refresh token
    user = User.query.filter_by(refresh_token=refresh_token).first()
    if not user or not user.verify_refresh_token(refresh_token):
        return jsonify({'error': 'Invalid refresh token'}), 401
    
    # Generate new access token
    access_token = JWTManager.generate_token(user.id, 'access')
    
    if request.is_json:
        return jsonify({'access_token': access_token})
    else:
        resp = make_response(jsonify({'success': True}))
        resp.set_cookie('access_token', access_token, max_age=24*60*60, httponly=True, secure=True)
        return resp

@auth.route('/settings/mfa', methods=['GET', 'POST'])
@jwt_required
def mfa_setup():
    if request.method == 'POST':
        token = request.form.get('token')
        if token and g.current_user.verify_totp(token):
            g.current_user.mfa_enabled = True
            db.session.commit()
            flash('Two-factor authentication enabled successfully', 'success')
        else:
            flash('Invalid verification code', 'danger')
    
    return redirect(url_for('auth.myaccount'))

@auth.route('/settings/mfa/disable', methods=['POST'])
@jwt_required
def mfa_disable():
    g.current_user.mfa_enabled = False
    db.session.commit()
    flash('Two-factor authentication disabled', 'success')
    return redirect(url_for('auth.myaccount'))

@auth.route('/settings/mfa/qrcode')
@jwt_required
def mfa_qrcode():
    if not g.current_user.mfa_secret:
        abort(404)
        
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(g.current_user.get_totp_uri())
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    output = BytesIO()
    img.save(output)
    output.seek(0)

    return send_file(output, mimetype='image/png')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # Check if already authenticated
    token = JWTManager.get_token_from_request()
    if token and JWTManager.decode_token(token):
        return redirect(url_for('main.dashboard'))

    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Send password reset email
            send_password_reset_email(user)
            flash('Password reset instructions sent to your email address.', 'info')
            return redirect(url_for('auth.login'))

    return render_template('reset_password_request.html', form=form)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Check if already authenticated
    jwt_token = JWTManager.get_token_from_request()
    if jwt_token and JWTManager.decode_token(jwt_token):
        return redirect(url_for('main.dashboard'))

    # Find user by reset token
    user = None
    for u in User.query.all():
        if u.reset_token == token:
            user = u
            break

    if user is None:
        flash('Invalid reset token', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if not user.verify_reset_token(token):
        flash('Expired reset token', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordWithTokenForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', form=form)