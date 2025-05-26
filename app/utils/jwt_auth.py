import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, request, jsonify, g
from app.models.user import User

class JWTManager:
    @staticmethod
    def generate_token(user_id, token_type='access', expires_delta=None):
        if expires_delta is None:
            expires_delta = timedelta(hours=24) if token_type == 'access' else timedelta(days=30)
        
        payload = {
            'user_id': user_id,
            'type': token_type,
            'exp': datetime.utcnow() + expires_delta,
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def decode_token(token):
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def get_token_from_request():
        # Check Authorization header first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        
        # Check cookies for web app compatibility
        return request.cookies.get('access_token')

def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = JWTManager.get_token_from_request()
        
        if not token:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({'error': 'Token required'}), 401
            # Redirect to login for web interface
            from flask import redirect, url_for
            return redirect(url_for('auth.login'))
        
        payload = JWTManager.decode_token(token)
        if not payload:
            if request.is_json:
                return jsonify({'error': 'Invalid token'}), 401
            from flask import redirect, url_for, flash
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Load user and store in Flask's g object
        user = User.query.get(payload['user_id'])
        if not user:
            if request.is_json:
                return jsonify({'error': 'User not found'}), 401
            from flask import redirect, url_for, flash
            flash('User account not found.', 'danger')
            return redirect(url_for('auth.login'))
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @jwt_required
    def decorated_function(*args, **kwargs):
        if not g.current_user.is_admin:
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            from flask import flash, redirect, url_for
            flash('Admin access required', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def printer_required(f):
    @wraps(f)
    @jwt_required
    def decorated_function(*args, **kwargs):
        if not (g.current_user.is_printer or g.current_user.is_admin):
            if request.is_json:
                return jsonify({'error': 'Printer access required'}), 403
            from flask import flash, redirect, url_for
            flash('Printer access required', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function