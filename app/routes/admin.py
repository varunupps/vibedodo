from functools import wraps
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.upload import Upload
from app.models.order import Order

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    uploads = Upload.query.order_by(Upload.date_posted.desc()).all()
    orders = Order.query.order_by(Order.date_ordered.desc()).all()
    
    return render_template('admin/dashboard.html', users=users, uploads=uploads, orders=orders)

@admin.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)
    
@admin.route('/admin/user/<int:user_id>/toggle-printer', methods=['POST'])
@login_required
@admin_required
def toggle_printer_role(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow toggling admin users
    if user.is_admin:
        flash('Cannot modify admin roles', 'danger')
        return redirect(url_for('admin.admin_users'))
    
    # Toggle printer role
    user.is_printer = not user.is_printer
    db.session.commit()
    
    if user.is_printer:
        flash(f'Printer role granted to {user.username}', 'success')
    else:
        flash(f'Printer role removed from {user.username}', 'success')
    
    return redirect(url_for('admin.admin_users'))

@admin.route('/admin/uploads')
@login_required
@admin_required
def admin_uploads():
    uploads = Upload.query.order_by(Upload.date_posted.desc()).all()
    return render_template('admin/uploads.html', uploads=uploads)