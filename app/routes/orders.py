from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, g, session
from app.utils.jwt_auth import jwt_required, printer_required
from app import db
from app.forms import OrderForm, AdminEditOrderForm, PaymentForm
from app.models.upload import Upload
from app.models.order import Order
from app.models.user import User
from app.models.delivery import DeliveryDay, TimeSlot

orders = Blueprint('orders', __name__)


@orders.route('/order/create/<int:upload_id>', methods=['GET', 'POST'])
@jwt_required
def create_order(upload_id):
    # Get the upload
    upload = Upload.query.get_or_404(upload_id)
    
    # Check if the current user is the owner of the upload
    if upload.user_id != g.current_user.id:
        abort(403)
        
    # Check if the upload is classified as non-gaming content
    if upload.classification == "OTHER":
        flash('Ordering postcards is not available for non-gaming content.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Time slots are now imported at the top of the file
    
    form = OrderForm()
    form.upload_id.data = upload_id
    
    # Pre-populate phone number field with user's phone number if available
    if request.method == 'GET' and g.current_user.phone_number:
        form.phone_number.data = g.current_user.phone_number
    
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
        # Get price based on selected size and quantity
        selected_size = form.size.data
        quantity = form.quantity.data

        # Check if client provided a price, otherwise use default price map
        if form.unit_price.data:
            try:
                # Use the price provided by the client
                unit_price = float(form.unit_price.data)
            except (ValueError, TypeError):
                # Fallback to server-side calculation if conversion fails
                price_map = {
                    'small': 5.00,   # Small (4" x 6") - $5 USD
                    'medium': 7.00,  # Medium (5" x 7") - $7 USD
                    'large': 10.00   # Large (6" x 11") - $10 USD
                }
                unit_price = price_map.get(selected_size, 5.00)
        else:
            # Fallback to server-side calculation if no price provided
            price_map = {
                'small': 5.00,   # Small (4" x 6") - $5 USD
                'medium': 7.00,  # Medium (5" x 7") - $7 USD
                'large': 10.00   # Large (6" x 11") - $10 USD
            }
            unit_price = price_map.get(selected_size, 5.00)

        total_price = unit_price * quantity
        
        # Verify selected time slot is still available
        selected_slot_id = form.time_slot_id.data
        selected_slot = TimeSlot.query.get(selected_slot_id)
        
        if not selected_slot or not selected_slot.is_available:
            flash('The selected delivery slot is no longer available. Please select a different time.', 'danger')
            return redirect(url_for('orders.create_order', upload_id=upload_id))
        
        # Store order details in session for payment processing
        session['order_data'] = {
            'user_id': g.current_user.id,
            'upload_id': upload_id,
            'size': selected_size,
            'quantity': quantity,
            'price': unit_price,
            'total_price': total_price,
            'address': form.address.data,
            'phone_number': form.phone_number.data,
            'time_slot_id': selected_slot_id
        }
        
        # Redirect to payment page
        return redirect(url_for('orders.payment'))
    
    # Define size dimensions and prices for the template
    size_info = {
        'small': {'dimensions': '4" x 6"', 'price': 5.00},
        'medium': {'dimensions': '5" x 7"', 'price': 7.00},
        'large': {'dimensions': '6" x 11"', 'price': 10.00}
    }
    
    return render_template('orders/create_order.html', upload=upload, form=form, size_info=size_info)


@orders.route('/payment', methods=['GET', 'POST'])
@jwt_required
def payment():
    # Check if order data exists in session
    if 'order_data' not in session:
        flash('No order data found. Please create an order first.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    order_data = session['order_data']
    form = PaymentForm()
    
    if form.validate_on_submit():
        # Test card validation - only check if card number is the test card
        card_number = form.card_number.data.replace(' ', '')  # Remove spaces
        
        if card_number == '4111111111111111':
            # Test card - payment successful
            # Create the order
            order = Order(
                user_id=order_data['user_id'],
                upload_id=order_data['upload_id'],
                size=order_data['size'],
                quantity=order_data['quantity'],
                price=order_data['price'],
                total_price=order_data['total_price'],
                address=order_data['address'],
                phone_number=order_data['phone_number'],
                time_slot_id=order_data['time_slot_id'],
                status='pending'
            )
            db.session.add(order)
            db.session.commit()
            
            # Clear order data from session
            session.pop('order_data', None)
            
            flash('Payment successful! Your postcard order has been placed.', 'success')
            return redirect(url_for('orders.my_orders'))
        else:
            # Invalid card number
            flash('Payment failed. Please check your card details.', 'danger')
    
    return render_template('orders/payment.html', form=form, order_data=order_data)


@orders.route('/my-orders')
@jwt_required
def my_orders():
    # Get all orders by the current user
    user_orders = Order.query.filter_by(user_id=g.current_user.id).order_by(Order.date_ordered.desc()).all()
    return render_template('orders/my_orders.html', orders=user_orders)

@orders.route('/order/<int:order_id>/details')
@jwt_required
def view_order_details(order_id):
    # Using direct database access for better performance
    from flask import current_app
    import sqlite3
    import os

    # Get the absolute path to the database file
    db_path = os.path.join(current_app.instance_path, 'site.db')

    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    cursor = conn.cursor()

    # SQL injection vulnerability - using string concatenation
    # Using SQLite-specific syntax for reserved keywords
    sql_query = f'SELECT * FROM [order] WHERE id = {order_id}'
    cursor.execute(sql_query)

    order_data = cursor.fetchone()

    if not order_data:
        abort(404)

    # Convert SQLite Row to a dictionary
    order_dict = dict(order_data)

    # Fetch related data
    cursor.execute(f"SELECT * FROM user WHERE id = {order_dict['user_id']}")
    user_data = cursor.fetchone()

    cursor.execute(f"SELECT * FROM upload WHERE id = {order_dict['upload_id']}")
    upload_data = cursor.fetchone()

    # Check if the current user is the owner of the order or an admin
    if order_dict['user_id'] != g.current_user.id and not g.current_user.is_admin:
        conn.close()
        abort(403)

    # Create a simple Order-like object with the necessary attributes
    class OrderObj:
        pass

    order = OrderObj()
    order.id = order_dict['id']
    order.user_id = order_dict['user_id']
    order.upload_id = order_dict['upload_id']
    order.address = order_dict['address']
    order.phone_number = order_dict['phone_number']
    order.date_ordered = datetime.strptime(order_dict['date_ordered'], '%Y-%m-%d %H:%M:%S.%f')
    order.size = order_dict['size']
    order.quantity = order_dict['quantity']
    order.price = order_dict['price']
    order.total_price = order_dict['total_price']
    order.status = order_dict['status']
    order.time_slot_id = order_dict.get('time_slot_id')
    order.approved_for_printing = bool(order_dict.get('approved_for_printing', 0))
    order.approved_by_id = order_dict.get('approved_by_id')
    order.printed = bool(order_dict.get('printed', 0))
    order.printed_by_id = order_dict.get('printed_by_id')
    order.printed_date = datetime.strptime(order_dict['printed_date'], '%Y-%m-%d %H:%M:%S.%f') if order_dict.get('printed_date') else None
    order.print_notes = order_dict.get('print_notes')

    # Add user and upload as attributes
    if user_data:
        class UserObj:
            pass
        order.user = UserObj()
        order.user.username = user_data['username']

    if upload_data:
        class UploadObj:
            pass
        order.upload = UploadObj()
        order.upload.image_filename = upload_data['image_filename']

    # Add delivery_info property to match the original Order model
    order.delivery_info = "Delivery information not available"

    conn.close()
    return render_template('orders/order_details.html', order=order)

# Admin routes for managing orders
@orders.route('/admin/orders')
@jwt_required
def admin_orders():
    # Check if user is admin
    if not g.current_user.is_admin:
        abort(403)
    
    # Get all orders
    all_orders = Order.query.order_by(Order.date_ordered.desc()).all()
    return render_template('admin/orders.html', orders=all_orders)

@orders.route('/admin/order/<int:order_id>/update/<string:status>', methods=['POST'])
@jwt_required
def update_order_status(order_id, status):
    # Check if user is admin
    if not g.current_user.is_admin:
        abort(403)
    
    # Valid statuses
    valid_statuses = ['pending', 'approved_for_printing', 'printed', 'shipped', 'completed', 'rejected']
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
        order.approved_by_id = g.current_user.id
    elif status == 'printed':
        order.printed = True
        order.printed_by_id = g.current_user.id
        order.printed_date = datetime.utcnow()
    
    # Add print notes if provided
    if request.form.get('print_notes'):
        order.print_notes = request.form.get('print_notes')
    
    db.session.commit()
    
    flash(f'Order {order_id} has been updated to {status}!', 'success')
    return redirect(url_for('orders.admin_orders'))

@orders.route('/admin/order/<int:order_id>/approve-for-printing', methods=['POST'])
@jwt_required
def approve_for_printing(order_id):
    # Check if user is admin
    if not g.current_user.is_admin:
        abort(403)
    
    # Get the order
    order = Order.query.get_or_404(order_id)
    
    # Update fields
    order.approved_for_printing = True
    order.approved_by_id = g.current_user.id
    order.status = 'approved_for_printing'
    
    # Add notes if provided
    if request.form.get('print_notes'):
        order.print_notes = request.form.get('print_notes')
    
    db.session.commit()
    
    flash(f'Order {order_id} has been approved for printing!', 'success')
    return redirect(url_for('orders.admin_orders'))

@orders.route('/admin/order/<int:order_id>/reject', methods=['POST'])
@jwt_required
def reject_order(order_id):
    # Check if user is admin
    if not g.current_user.is_admin:
        abort(403)
    
    # Get the order
    order = Order.query.get_or_404(order_id)
    
    # Update fields
    order.approved_for_printing = False
    order.approved_by_id = g.current_user.id
    order.status = 'rejected'
    
    # Add rejection reason if provided
    if request.form.get('rejection_reason'):
        order.print_notes = f"REJECTED: {request.form.get('rejection_reason')}"
    else:
        order.print_notes = "REJECTED: No reason provided"
    
    db.session.commit()
    
    flash(f'Order {order_id} has been rejected!', 'warning')
    return redirect(url_for('orders.admin_orders'))

# Printer Routes
@orders.route('/printer/dashboard')
@jwt_required
@printer_required
def printer_dashboard():
    # Get all orders approved for printing but not yet printed
    # Explicitly exclude rejected orders
    approved_orders = Order.query.filter(
        Order.approved_for_printing == True,
        Order.printed == False,
        Order.status != 'rejected'
    ).order_by(Order.date_ordered.asc()).all()
    
    # Get all orders that this printer has printed
    printed_orders = Order.query.filter_by(
        printed=True,
        printed_by_id=g.current_user.id
    ).order_by(Order.printed_date.desc()).all()
    
    return render_template('orders/printer_dashboard.html', 
                          approved_orders=approved_orders,
                          printed_orders=printed_orders)

@orders.route('/printer/order/<int:order_id>/mark-printed', methods=['POST'])
@jwt_required
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
    order.printed_by_id = g.current_user.id
    order.printed_date = datetime.utcnow()
    order.status = 'printed'
    
    db.session.commit()
    
    flash(f'Order {order_id} has been marked as printed!', 'success')
    return redirect(url_for('orders.printer_dashboard'))

@orders.route('/admin/order/<int:order_id>/edit', methods=['GET', 'POST'])
@jwt_required
def edit_order(order_id):
    # Check if user is admin
    if not g.current_user.is_admin:
        abort(403)

    # Get the order
    order = Order.query.get_or_404(order_id)

    # Create form
    form = AdminEditOrderForm()

    # Get available delivery time slots for the form
    available_slots = []

    # Get all active delivery days with their time slots
    delivery_days = DeliveryDay.query.filter_by(is_active=True).filter(DeliveryDay.date >= datetime.utcnow().date()).order_by(DeliveryDay.date).all()

    for day in delivery_days:
        # Get available time slots for this day
        slots = TimeSlot.query.filter_by(delivery_day_id=day.id, is_active=True).all()
        for slot in slots:
            # We include all slots regardless of capacity for existing orders
            slot_text = f"{day.formatted_date}, {slot.formatted_time_range}"
            available_slots.append((slot.id, slot_text))

    # Add "None" option for delivery time
    available_slots.insert(0, (-1, 'No delivery time scheduled'))

    # Update form choices
    form.time_slot_id.choices = available_slots

    # If it's a POST request and form is valid
    if form.validate_on_submit():
        # Calculate total price based on size and quantity
        price_map = {
            'small': 5.00,   # Small (4" x 6") - $5 USD
            'medium': 7.00,  # Medium (5" x 7") - $7 USD
            'large': 10.00   # Large (6" x 11") - $10 USD
        }
        selected_size = form.size.data
        quantity = form.quantity.data
        unit_price = price_map.get(selected_size, 5.00)
        total_price = unit_price * quantity

        # Update the order
        order.size = selected_size
        order.quantity = quantity
        order.price = unit_price
        order.total_price = total_price
        order.address = form.address.data
        order.phone_number = form.phone_number.data
        order.status = form.status.data

        # Set time slot if one is selected (not -1)
        if form.time_slot_id.data != -1:
            order.time_slot_id = form.time_slot_id.data
        else:
            order.time_slot_id = None

        # Update print notes
        if form.print_notes.data:
            order.print_notes = form.print_notes.data

        # Set additional fields based on status
        if form.status.data == 'approved_for_printing' and not order.approved_for_printing:
            order.approved_for_printing = True
            order.approved_by_id = g.current_user.id
        elif form.status.data == 'printed' and not order.printed:
            order.printed = True
            order.printed_by_id = g.current_user.id
            order.printed_date = datetime.utcnow()

        db.session.commit()
        flash(f'Order #{order_id} has been updated!', 'success')
        return redirect(url_for('orders.admin_orders'))

    # If it's a GET request, populate the form with current data
    elif request.method == 'GET':
        form.size.data = order.size
        form.quantity.data = order.quantity
        form.address.data = order.address
        form.phone_number.data = order.phone_number
        form.status.data = order.status

        if order.time_slot_id:
            form.time_slot_id.data = order.time_slot_id
        else:
            form.time_slot_id.data = -1

        if order.print_notes:
            form.print_notes.data = order.print_notes

    return render_template('admin/edit_order.html', order=order, form=form)