# Routes package
from app.routes.auth import auth
from app.routes.main import main
from app.routes.admin import admin
from app.routes.orders import orders

def init_app(app):
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(orders)
