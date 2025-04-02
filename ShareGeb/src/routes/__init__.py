# src/routes/__init__.py
from src.routes.users import users_bp
from src.routes.home import home_bp
from src.routes.book_ride import book_ride_bp
from src.routes.cancel_ride import cancel_ride_bp
from src.routes.discount import discount_bp
from src.routes.errors import errors_bp
from src.routes.payment import payment_bp
from src.routes.partners import partners_bp
from src.routes.support import support_bp
from src.routes.chatbot import chatbot_bp

# Export all blueprints
__all__ = [
    'book_ride_bp',
    'cancel_ride_bp',
    'discount_bp',
    'errors_bp',
    'home_bp',
    'payment_bp',
    'users_bp',
    'partners_bp',
    'support_bp',
    'chatbot_bp'
]