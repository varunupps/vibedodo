from functools import wraps
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.upload import Upload
from app.models.order import Order
from app.models.delivery import DeliveryDay, TimeSlot
from app.forms import DeliveryDayForm, TimeSlotForm, ResetPasswordForm

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

@admin.route('/admin/delivery', methods=['GET'])
@login_required
@admin_required
def admin_delivery():
    # Get delivery days and time slots
    delivery_days = DeliveryDay.query.order_by(DeliveryDay.date).all()
    
    # Count orders per time slot for display
    time_slots = TimeSlot.query.all()
    slot_stats = {}
    
    for slot in time_slots:
        orders_count = Order.query.filter_by(time_slot_id=slot.id).count()
        slot_stats[slot.id] = {
            'orders_count': orders_count,
            'capacity': slot.max_orders,
            'utilization': round((orders_count / slot.max_orders) * 100) if slot.max_orders > 0 else 0
        }
    
    return render_template('admin/delivery.html', 
                          delivery_days=delivery_days,
                          slot_stats=slot_stats)

@admin.route('/admin/delivery/day/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_delivery_day():
    form = DeliveryDayForm()
    
    if form.validate_on_submit():
        delivery_day = DeliveryDay(
            date=form.date.data,
            is_active=form.is_active.data,
            max_deliveries=form.max_deliveries.data
        )
        
        db.session.add(delivery_day)
        db.session.commit()
        flash('Delivery day added successfully', 'success')
        return redirect(url_for('admin.admin_delivery'))
    
    return render_template('admin/delivery_day_form.html', form=form, title='Add Delivery Day')

@admin.route('/admin/delivery/day/<int:day_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_delivery_day(day_id):
    delivery_day = DeliveryDay.query.get_or_404(day_id)
    form = DeliveryDayForm(obj=delivery_day)
    
    if form.validate_on_submit():
        delivery_day.date = form.date.data
        delivery_day.is_active = form.is_active.data
        delivery_day.max_deliveries = form.max_deliveries.data
        
        db.session.commit()
        flash('Delivery day updated successfully', 'success')
        return redirect(url_for('admin.admin_delivery'))
        
    return render_template('admin/delivery_day_form.html', form=form, title='Edit Delivery Day')

@admin.route('/admin/delivery/day/<int:day_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_delivery_day(day_id):
    delivery_day = DeliveryDay.query.get_or_404(day_id)
    
    # Check if there are orders using this day's time slots
    slots = TimeSlot.query.filter_by(delivery_day_id=day_id).all()
    slot_ids = [slot.id for slot in slots]
    
    if slot_ids:
        orders = Order.query.filter(Order.time_slot_id.in_(slot_ids)).count()
        if orders > 0:
            flash(f'Cannot delete: {orders} orders are scheduled for this delivery day', 'danger')
            return redirect(url_for('admin.admin_delivery'))
    
    # Delete the day and its slots
    db.session.delete(delivery_day)
    db.session.commit()
    
    flash('Delivery day deleted successfully', 'success')
    return redirect(url_for('admin.admin_delivery'))

@admin.route('/admin/delivery/timeslot/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_time_slot():
    form = TimeSlotForm()
    
    # Check if day_id was provided in the URL
    day_id = request.args.get('day_id', type=int)
    selected_day = None
    
    if day_id:
        selected_day = DeliveryDay.query.get(day_id)
    
    # Populate delivery day choices
    days = DeliveryDay.query.order_by(DeliveryDay.date).all()
    form.delivery_day_id.choices = [(day.id, day.formatted_date) for day in days]
    
    # Pre-select the day if it was provided in the URL
    if request.method == 'GET' and selected_day:
        form.delivery_day_id.data = selected_day.id
    
    if form.validate_on_submit():
        time_slot = TimeSlot(
            delivery_day_id=form.delivery_day_id.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            is_active=form.is_active.data,
            max_orders=form.max_orders.data
        )
        
        db.session.add(time_slot)
        db.session.commit()
        flash('Time slot added successfully', 'success')
        return redirect(url_for('admin.admin_delivery'))
    
    return render_template('admin/time_slot_form.html', form=form, title='Add Time Slot')

@admin.route('/admin/delivery/timeslot/<int:slot_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_time_slot(slot_id):
    time_slot = TimeSlot.query.get_or_404(slot_id)
    form = TimeSlotForm(obj=time_slot)
    
    # Populate delivery day choices
    days = DeliveryDay.query.order_by(DeliveryDay.date).all()
    form.delivery_day_id.choices = [(day.id, day.formatted_date) for day in days]
    
    if form.validate_on_submit():
        time_slot.delivery_day_id = form.delivery_day_id.data
        time_slot.start_time = form.start_time.data
        time_slot.end_time = form.end_time.data
        time_slot.is_active = form.is_active.data
        time_slot.max_orders = form.max_orders.data
        
        db.session.commit()
        flash('Time slot updated successfully', 'success')
        return redirect(url_for('admin.admin_delivery'))
        
    return render_template('admin/time_slot_form.html', form=form, title='Edit Time Slot')

@admin.route('/admin/delivery/timeslot/<int:slot_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_time_slot(slot_id):
    time_slot = TimeSlot.query.get_or_404(slot_id)
    
    # Check if there are orders using this time slot
    orders_count = Order.query.filter_by(time_slot_id=slot_id).count()
    if orders_count > 0:
        flash(f'Cannot delete: {orders_count} orders are scheduled for this time slot', 'danger')
        return redirect(url_for('admin.admin_delivery'))
    
    # Delete the time slot
    db.session.delete(time_slot)
    db.session.commit()
    
    flash('Time slot deleted successfully', 'success')
    return redirect(url_for('admin.admin_delivery'))

@admin.route('/admin/user/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(f'Password for {user.username} has been reset successfully', 'success')
        return redirect(url_for('admin.admin_users'))
    
    return render_template('admin/reset_password.html', form=form, user=user)