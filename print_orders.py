from app import create_app, db
from app.models.order import Order

app = create_app()

with app.app_context():
    orders = Order.query.all()
    
    print(f"Total orders: {len(orders)}")
    print("-" * 80)
    
    for order in orders:
        print(f"Order ID: {order.id}")
        print(f"User ID: {order.user_id}")
        print(f"Upload ID: {order.upload_id}")
        print(f"Address: {order.address}")
        print(f"Phone: {order.phone_number}")
        print(f"Date ordered: {order.date_ordered}")
        print(f"Size: {order.size}")
        print(f"Quantity: {order.quantity}")
        print(f"Price: ${order.price:.2f}")
        print(f"Total price: ${order.total_price:.2f}")
        print(f"Status: {order.status}")
        print(f"Time slot ID: {order.time_slot_id}")
        print(f"Approved for printing: {order.approved_for_printing}")
        print(f"Approved by ID: {order.approved_by_id}")
        print(f"Printed: {order.printed}")
        print(f"Printed by ID: {order.printed_by_id}")
        print(f"Printed date: {order.printed_date}")
        print(f"Print notes: {order.print_notes}")
        print("-" * 80)