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
        
    # Check if the upload is classified as non-gaming content
    if upload.classification == "OTHER":
        flash('Ordering postcards is not available for non-gaming content.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Import here to avoid circular imports
    from app.models.delivery import DeliveryDay, TimeSlot
    
    form = OrderForm()
    form.upload_id.data = upload_id
    
    # Pre-populate phone number field with user's phone number if available
    if request.method == 'GET' and current_user.phone_number:
        form.phone_number.data = current_user.phone_number
    
    # Populate time slot options
    available_slots = []
    
    # Get all active delivery days with their time slots
    delivery_days = DeliveryDay.query.filter_by(is_active=True).filter(DeliveryDay.date >= datetime.utcnow().date()).order_by(DeliveryDay.date).all()
    
    for day in delivery_days:
        # Get available time slots for this day
        slots = TimeSlot.query.filter_by(delivery_day_id=day.id, is_active=True).all()
        for slot in slots:
            # Check if the slot has capacity
            if slot.current_orders_count < slot.max_orders:
                slot_text = f"{day.formatted_date}, {slot.formatted_time_range}"
                available_slots.append((slot.id, slot_text))
    
    # Update form choices
    if available_slots:
        form.time_slot_id.choices = available_slots
    else:
        # No slots available
        form.time_slot_id.choices = [(-1, 'No delivery slots available')]
        if request.method == 'GET':
            flash('There are currently no available delivery slots. Please try again later.', 'warning')
    
    if form.validate_on_submit():
        # Calculate price based on selected size
        price_map = {
            'small': 5.00,   # Small (4" x 6") - $5 USD
            'medium': 7.00,  # Medium (5" x 7") - $7 USD
            'large': 10.00   # Large (6" x 11") - $10 USD
        }
        selected_size = form.size.data
        quantity = form.quantity.data
        unit_price = price_map.get(selected_size, 5.00)
        total_price = unit_price * quantity
        
        # Verify selected time slot is still available
        selected_slot_id = form.time_slot_id.data
        selected_slot = TimeSlot.query.get(selected_slot_id)
        
        if not selected_slot or not selected_slot.is_available:
            flash('The selected delivery slot is no longer available. Please select a different time.', 'danger')
            return redirect(url_for('orders.create_order', upload_id=upload_id))
        
        order = Order(
            user_id=current_user.id,
            upload_id=upload_id,
            size=selected_size,
            quantity=quantity,
            price=unit_price,
            total_price=total_price,
            address=form.address.data,
            phone_number=form.phone_number.data,
            time_slot_id=selected_slot_id,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        flash('Your postcard order has been placed!', 'success')
        return redirect(url_for('orders.my_orders'))
    
    # Define size dimensions and prices for the template
    size_info = {
        'small': {'dimensions': '4" x 6"', 'price': 5.00},
        'medium': {'dimensions': '5" x 7"', 'price': 7.00},
        'large': {'dimensions': '6" x 11"', 'price': 10.00}
    }
    
    return render_template('orders/create_order.html', upload=upload, form=form, size_info=size_info)

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