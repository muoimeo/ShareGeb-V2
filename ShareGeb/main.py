import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Tải biến môi trường từ file .env trước khi import bất kỳ module nào khác
basedir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(basedir, '..'))

# Thử tải từ cả hai vị trí có thể chứa file .env
if os.path.exists(os.path.join(basedir, '.env')):
    load_dotenv(os.path.join(basedir, '.env'))
    print(f"Loaded .env from {basedir}")
if os.path.exists(os.path.join(project_root, '.env')):
    load_dotenv(os.path.join(project_root, '.env'))
    print(f"Loaded .env from {project_root}")

# In các biến môi trường để debug
print(f"GEMINI_API_KEY is set: {os.getenv('GEMINI_API_KEY') is not None}")
print(f"Current directory: {basedir}")
print(f"Project root: {project_root}")

# Import các module sau khi đã tải biến môi trường
from flask import Flask, render_template, url_for, redirect, session, flash, request
from flask_login import LoginManager, current_user
from werkzeug.security import generate_password_hash
from src.models import db, User
from src.routes.users import users_bp
from src.routes.home import home_bp
from src.routes.book_ride import book_ride_bp
from src.routes.payment import payment_bp
from src.routes.profile import profile_bp
from src.routes.discount import discount_bp
from src.routes.partners import partners_bp
from src.routes.support import support_bp
from src.routes.chatbot import chatbot_bp

# Initialize Flask app
app = Flask(__name__, 
    template_folder='src/templates',
    static_folder='static'
)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:MinhDZ3009@localhost/sharegeb?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 3600,
    'pool_timeout': 900,
    'pool_size': 10,
    'max_overflow': 5
}
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'users.login'
login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(users_bp)
app.register_blueprint(home_bp)
app.register_blueprint(book_ride_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(discount_bp)
app.register_blueprint(partners_bp)
app.register_blueprint(support_bp)
app.register_blueprint(chatbot_bp)

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)