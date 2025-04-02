from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Khởi tạo SQLAlchemy
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('user', 'driver', 'admin'), default='user')
    status = db.Column(db.Enum('active', 'inactive', 'suspended'), default='active')
    verification_status = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    last_login = db.Column(db.TIMESTAMP, nullable=True)
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    interests = db.Column(db.String(255), nullable=True)
    avatar = db.Column(db.String(255), default='basic_avatar.png')
    rating = db.Column(db.Float, default=0.0)
    ride_count = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Numeric(10, 2), default=0.00)
    wallet_balance = db.Column(db.Numeric(10, 2), default=0.00)
    preferred_payment_method = db.Column(db.Enum('cash', 'credit_card', 'wallet', 'bank_account'), default='cash')

    # Relationships
    driver = db.relationship('Driver', backref='user', uselist=False, cascade="all, delete")
    ride_passengers = db.relationship('RidePassenger', backref='user', cascade="all, delete")
    notifications = db.relationship('Notification', backref='user', cascade="all, delete")
    bank_accounts = db.relationship('BankAccount', backref='user', lazy=True, cascade="all, delete")
    wallets = db.relationship('Wallet', backref='user', lazy=True, cascade="all, delete")
    credit_cards = db.relationship('CreditCard', backref='user', lazy=True, cascade="all, delete")
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade="all, delete")

    def get_id(self):
        return str(self.user_id)

    @property
    def is_active(self):
        return self.status == 'active'

    def set_password(self, password):
        try:
            self.password_hash = generate_password_hash(password)
        except Exception as e:
            raise ValueError(f"Error setting password: {str(e)}")

    def check_password(self, password):
        if not password or not self.password_hash:
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            print("Error checking password")
            return False

    @property
    def member_rank(self):
        if self.ride_count < 7:
            return 'Iron Member'
        elif self.ride_count < 20:
            return 'Bronze Member'
        elif self.ride_count < 40:
            return 'Silver Member'
        elif self.ride_count < 70:
            return 'Gold Member'
        elif self.ride_count < 100:
            return 'Diamond Member'
        else:
            return 'VIP Member'


class Driver(db.Model):
    __tablename__ = 'Drivers'
    driver_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), unique=True, nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.Enum('available', 'busy', 'inactive'), default='available')

    # Relationships
    vehicles = db.relationship('Vehicle', backref='driver', cascade="all, delete")
    rides = db.relationship('Ride', backref='driver', cascade="all, delete")


class Vehicle(db.Model):
    __tablename__ = 'Vehicles'
    vehicle_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('Drivers.driver_id', ondelete="CASCADE"), nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)


class Ride(db.Model):
    __tablename__ = 'Rides'
    ride_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('Drivers.driver_id', ondelete="SET NULL"))
    status = db.Column(db.Enum('requested', 'accepted', 'ongoing', 'completed', 'cancelled'), default='requested')
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    started_at = db.Column(db.TIMESTAMP, nullable=True)
    completed_at = db.Column(db.TIMESTAMP, nullable=True)
    cancellation_reason = db.Column(db.String(255), nullable=True)

    # Relationships
    passengers = db.relationship('RidePassenger', backref='ride', cascade="all, delete")
    ratings = db.relationship('Rating', backref='ride', cascade="all, delete")
    chat_messages = db.relationship('ChatMessage', backref='ride', cascade="all, delete")


class RidePassenger(db.Model):
    __tablename__ = 'Ride_Passengers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('Rides.ride_id', ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    pickup_location = db.Column(db.String(255), nullable=False)
    dropoff_location = db.Column(db.String(255), nullable=False)
    distance_km = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    fare = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('requested', 'onboard', 'completed', 'cancelled'), default='requested')
    joined_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # Relationships
    payments = db.relationship('Payment', backref='ride_passenger', cascade="all, delete")
    discount_usages = db.relationship('DiscountUsage', backref='ride_passenger', cascade="all, delete")


class Transaction(db.Model):
    __tablename__ = 'Transactions'
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Enum('deposit', 'withdrawal', 'payment', 'refund', 'transfer'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    balance_before = db.Column(db.Numeric(10, 2), nullable=False)
    balance_after = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'completed', 'failed', 'cancelled'), default='pending')
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    completed_at = db.Column(db.TIMESTAMP, nullable=True)

    # Relationships
    payment = db.relationship('Payment', backref='transaction', uselist=False, cascade="all, delete")


class Payment(db.Model):
    __tablename__ = 'Payments'
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ride_passenger_id = db.Column(db.Integer, db.ForeignKey('Ride_Passengers.id', ondelete="CASCADE"), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('Transactions.transaction_id', ondelete="CASCADE"), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.Enum('cash', 'credit_card', 'wallet'), nullable=False)
    payment_status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', 'refunded'), default='pending')
    card_id = db.Column(db.Integer, db.ForeignKey('Credit_Cards.card_id'), nullable=True)
    payment_gateway = db.Column(db.String(50), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    paid_at = db.Column(db.TIMESTAMP, nullable=True)
    refunded_at = db.Column(db.TIMESTAMP, nullable=True)

    # Relationships
    refunds = db.relationship('PaymentRefund', backref='payment', cascade="all, delete")


class PaymentRefund(db.Model):
    __tablename__ = 'Payment_Refunds'
    refund_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('Payments.payment_id', ondelete="CASCADE"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed'), default='pending')
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    processed_at = db.Column(db.TIMESTAMP, nullable=True)


class Rating(db.Model):
    __tablename__ = 'Ratings'
    rating_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('Rides.ride_id', ondelete="CASCADE"), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    ratee_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    __table_args__ = (
        db.UniqueConstraint('ride_id', 'rater_id', 'ratee_id', name='unique_rating'),
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range')
    )

    # Relationships
    rater = db.relationship('User', foreign_keys=[rater_id], backref='ratings_given')
    ratee = db.relationship('User', foreign_keys=[ratee_id], backref='ratings_received')


class ChatMessage(db.Model):
    __tablename__ = 'Chat_Messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    ride_id = db.Column(db.Integer, db.ForeignKey('Rides.ride_id', ondelete="CASCADE"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='messages_sent')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='messages_received')


class Notification(db.Model):
    __tablename__ = 'Notifications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())


class Discount(db.Model):
    __tablename__ = 'Discounts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    max_discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    valid_from = db.Column(db.Date, nullable=False)
    valid_to = db.Column(db.Date, nullable=False)
    max_usage = db.Column(db.Integer, default=1)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # Relationships
    discount_usages = db.relationship('DiscountUsage', backref='discount', cascade="all, delete")


class DiscountUsage(db.Model):
    __tablename__ = 'Discount_Usage'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ride_passenger_id = db.Column(db.Integer, db.ForeignKey('Ride_Passengers.id', ondelete="CASCADE"), nullable=False)
    discount_id = db.Column(db.Integer, db.ForeignKey('Discounts.id', ondelete="CASCADE"), nullable=False)
    used_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())


class BankAccount(db.Model):
    __tablename__ = 'Bank_Accounts'
    account_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    account_holder_name = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    last_4_digits = db.Column(db.String(4), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def __init__(self, user_id, bank_name, account_number, account_holder_name):
        self.user_id = user_id
        self.bank_name = bank_name
        self.account_number = account_number
        self.last_4_digits = account_number[-4:]
        self.account_holder_name = account_holder_name


class Wallet(db.Model):
    __tablename__ = 'Wallets'
    wallet_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    wallet_type = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00)
    currency = db.Column(db.String(3), default='VND')
    status = db.Column(db.Enum('active', 'frozen', 'closed'), default='active')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    last_transaction_at = db.Column(db.TIMESTAMP, nullable=True)

    def __init__(self, user_id, wallet_type, account_number, balance=0.00, currency='VND', status='active', is_default=False):
        self.user_id = user_id
        self.wallet_type = wallet_type
        self.account_number = account_number
        self.balance = balance
        self.currency = currency
        self.status = status
        self.is_default = is_default


class CreditCard(db.Model):
    __tablename__ = 'Credit_Cards'
    card_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete="CASCADE"), nullable=False)
    card_number = db.Column(db.String(16), nullable=False)
    last_4_digits = db.Column(db.String(4), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    card_holder_name = db.Column(db.String(255), nullable=False)
    card_type = db.Column(db.String(50), nullable=False)
    cvv = db.Column(db.String(4), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    # Relationships
    payments = db.relationship('Payment', backref='credit_card', lazy=True)

    def __init__(self, user_id, card_number, expiry_date, card_holder_name, card_type):
        self.user_id = user_id
        self.card_number = card_number
        self.last_4_digits = card_number[-4:]
        self.expiry_date = expiry_date
        self.card_holder_name = card_holder_name
        self.card_type = card_type
        self.cvv = card_number[-4:]