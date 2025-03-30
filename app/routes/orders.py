from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.forms import OrderForm
from app.models.upload import Upload
from app.models.order import Order

orders = Blueprint('orders', __name__)

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
    valid_statuses = ['pending', 'shipped', 'completed']
    if status not in valid_statuses:
        flash('Invalid status!', 'danger')
        return redirect(url_for('orders.admin_orders'))
    
    # Get the order
    order = Order.query.get_or_404(order_id)
    
    # Update status
    order.status = status
    db.session.commit()
    
    flash(f'Order {order_id} has been updated to {status}!', 'success')
    return redirect(url_for('orders.admin_orders'))