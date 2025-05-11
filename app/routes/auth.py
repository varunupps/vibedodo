from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file, abort
from flask_login import login_user, logout_user, current_user, login_required
from app.models.user import User
from app.forms import RegistrationForm, LoginForm, TOTPForm, MFASetupForm, RequestPasswordResetForm, ResetPasswordWithTokenForm
from app import db
from app.utils.email import send_password_reset_email
import pyotp
import qrcode
from io import BytesIO

auth = Blueprint('auth', __name__)

@auth.route('/myaccount', methods=['GET', 'POST'])
@login_required
def myaccount():
    # Make sure MFA secret is generated if it doesn't exist
    if not current_user.mfa_secret:
        current_user.mfa_secret = pyotp.random_base32()
        db.session.commit()
        
    return render_template('myaccount.html')

@auth.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        country = request.form.get('country')
        phone_number = request.form.get('phone_number')
        
        # Basic validation
        if country and phone_number:
            # Update user profile
            current_user.country = country
            current_user.phone_number = phone_number
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        else:
            flash('Please provide both country and phone number.', 'danger')
            
    return redirect(url_for('auth.myaccount'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
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
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if user.mfa_enabled:
                # Store user ID in session for MFA step
                session['user_id'] = user.id
                session['remember'] = form.remember.data
                session['next'] = request.args.get('next')
                return redirect(url_for('auth.login_mfa'))
            else:
                # Normal login without MFA
                login_user(user, remember=form.remember.data)
                
                # Set session flag for first-time welcome dialog if user hasn't seen it
                if not user.has_seen_welcome:
                    session['show_welcome_dialog'] = True
                    
                # VULNERABILITY: Open Redirect - accepts any external URL without validation
                next_page = request.args.get('next') or request.args.get('redirect_url')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('login.html', form=form)

@auth.route('/login/mfa', methods=['GET', 'POST'])
def login_mfa():
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
        
    form = TOTPForm()
    if form.validate_on_submit():
        user = User.query.get(session['user_id'])
        if user and user.verify_totp(form.token.data):
            login_user(user, remember=session.get('remember', False))
            session.pop('user_id', None)
            session.pop('remember', None)
            
            # Set session flag for first-time welcome dialog if user hasn't seen it
            if not user.has_seen_welcome:
                session['show_welcome_dialog'] = True
                
            # VULNERABILITY: Open Redirect - accepts any external URL without validation
            next_page = session.pop('next', None) or request.args.get('redirect_url')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid authentication code', 'danger')
            
    return render_template('login_mfa.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/settings/mfa', methods=['GET', 'POST'])
@login_required
def mfa_setup():
    if request.method == 'POST':
        token = request.form.get('token')
        if token and current_user.verify_totp(token):
            current_user.mfa_enabled = True
            db.session.commit()
            flash('Two-factor authentication enabled successfully', 'success')
        else:
            flash('Invalid verification code', 'danger')
    
    return redirect(url_for('auth.myaccount'))

@auth.route('/settings/mfa/disable', methods=['POST'])
@login_required
def mfa_disable():
    current_user.mfa_enabled = False
    db.session.commit()
    flash('Two-factor authentication disabled', 'success')
    return redirect(url_for('auth.myaccount'))

@auth.route('/settings/mfa/qrcode')
@login_required
def mfa_qrcode():
    if not current_user.mfa_secret:
        abort(404)
        
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(current_user.get_totp_uri())
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    output = BytesIO()
    img.save(output)
    output.seek(0)

    return send_file(output, mimetype='image/png')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
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
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
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
