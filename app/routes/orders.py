from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.forms import OrderForm
from app.models.upload import Upload
from app.models.order import Order
from app.models.user import User

orders = Blueprint('orders', __name__)

def printer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_printer or current_user.is_admin):
            flash('Printer access required', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@orders.route('/order/create/<int:upload_id>', methods=['GET', 'POST'])
@login_required
def create_order(upload_id):
    # Get the upload
    upload = Upload.query.get_or_404(upload_id)
    
    # Check if the current user is the owner of the upload
    if upload.user_id != current_user.id:
        abort(403)
    
    form = OrderForm()
    form.upload_id.data = upload_id
    
    if form.validate_on_submit():
        order = Order(
            user_id=current_user.id,
            upload_id=upload_id,
            address=form.address.data,
            phone_number=form.phone_number.data,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        flash('Your postcard order has been placed!', 'success')
        return redirect(url_for('orders.my_orders'))
    
    # Pass pricing information to template
    price = 10.00  # $10 USD for each postcard
    
    return render_template('orders/create_order.html', upload=upload, form=form, price=price)

@orders.route('/my-orders')
@login_required
def my_orders():
    # Get all orders by the current user
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_ordered.desc()).all()
    return render_template('orders/my_orders.html', orders=user_orders)

# Admin routes for managing orders
@orders.route('/admin/orders')
@login_required
def admin_orders():
    # Check if user is admin
    if not current_user.is_admin:
        abort(403)
    
    # Get all orders
    all_orders = Order.query.order_by(Order.date_ordered.desc()).all()
    return render_template('admin/orders.html', orders=all_orders)

@orders.route('/admin/order/<int:order_id>/update/<string:status>', methods=['POST'])
@login_required
def update_order_status(order_id, status):
    # Check if user is admin
    if not current_user.is_admin:
        abort(403)
    
    # Valid statuses
    valid_statuses = ['pending', 'approved_for_printing', 'printed', 'shipped', 'completed']
    if status not in valid_statuses:
        flash('Invalid status!', 'danger')
        return redirect(url_for('orders.admin_orders'))
    
    # Get the order
    order = Order.query.get_or_404(order_id)
    
    # Update status
    order.status = status
    
    # Additional fields based on status
    if status == 'approved_for_printing':
        order.approved_for_printing = True
        order.approved_by_id = current_user.id
    elif status == 'printed':
        order.printed = True
        order.printed_by_id = current_user.id
        order.printed_date = datetime.utcnow()
    
    # Add print notes if provided
    if request.form.get('print_notes'):
        order.print_notes = request.form.get('print_notes')
    
    db.session.commit()
    
    flash(f'Order {order_id} has been updated to {status}!', 'success')
    return redirect(url_for('orders.admin_orders'))

@orders.route('/admin/order/<int:order_id>/approve-for-printing', methods=['POST'])
@login_required
def approve_for_printing(order_id):
    # Check if user is admin
    if not current_user.is_admin:
        abort(403)
    
    # Get the order
    order = Order.query.get_or_404(order_id)
    
    # Update fields
    order.approved_for_printing = True
    order.approved_by_id = current_user.id
    order.status = 'approved_for_printing'
    
    # Add notes if provided
    if request.form.get('print_notes'):
        order.print_notes = request.form.get('print_notes')
    
    db.session.commit()
    
    flash(f'Order {order_id} has been approved for printing!', 'success')
    return redirect(url_for('orders.admin_orders'))

# Printer Routes
@orders.route('/printer/dashboard')
@login_required
@printer_required
def printer_dashboard():
    # Get all orders approved for printing but not yet printed
    approved_orders = Order.query.filter_by(
        approved_for_printing=True, 
        printed=False
    ).order_by(Order.date_ordered.asc()).all()
    
    # Get all orders that this printer has printed
    printed_orders = Order.query.filter_by(
        printed=True,
        printed_by_id=current_user.id
    ).order_by(Order.printed_date.desc()).all()
    
    return render_template('orders/printer_dashboard.html', 
                          approved_orders=approved_orders,
                          printed_orders=printed_orders)

@orders.route('/printer/order/<int:order_id>/mark-printed', methods=['POST'])
@login_required
@printer_required
def mark_as_printed(order_id):
    # Get the order
    order = Order.query.get_or_404(order_id)
    
    # Verify the order is approved for printing and not already printed
    if not order.approved_for_printing or order.printed:
        flash('Order cannot be marked as printed!', 'danger')
        return redirect(url_for('orders.printer_dashboard'))
    
    # Mark as printed
    order.printed = True
    order.printed_by_id = current_user.id
    order.printed_date = datetime.utcnow()
    order.status = 'printed'
    
    db.session.commit()
    
    flash(f'Order {order_id} has been marked as printed!', 'success')
    return redirect(url_for('orders.printer_dashboard'))