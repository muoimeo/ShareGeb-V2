from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from src.models import db, User, Discount, CreditCard, Wallet, BankAccount
from datetime import datetime
from sqlalchemy import and_

book_ride_bp = Blueprint('book_ride', __name__)

@book_ride_bp.route('/book-ride', methods=['GET', 'POST'])
@login_required
def book_ride():
    if request.method == 'POST':
        pickup = request.form.get('pickup')
        dropoff = request.form.get('dropoff')
        # Add logic to save to database here
        
        # Lấy thông tin giảm giá nếu có
        discount_id = session.get('discount_id')
        
        # Xóa thông tin giảm giá đã sử dụng khỏi session
        if discount_id:
            session.pop('discount_code', None)
            session.pop('discount_percentage', None)
            session.pop('discount_max_amount', None)
            session.pop('discount_id', None)
            session.modified = True
        
        return render_template('book_ride.html', message="Ride booked!", user=current_user)
    
    # Lấy thông tin phương thức thanh toán của user
    credit_cards = CreditCard.query.filter_by(user_id=current_user.user_id).all()
    wallets = Wallet.query.filter_by(user_id=current_user.user_id).all()
    bank_accounts = BankAccount.query.filter_by(user_id=current_user.user_id).all()
    
    # Lấy mã giảm giá đang áp dụng từ session nếu có
    discount_code = session.get('discount_code')
    discount_percentage = session.get('discount_percentage')
    max_discount = session.get('discount_max_amount')
    discount_applied = discount_code is not None
    
    # Lấy danh sách mã giảm giá khả dụng
    current_date = datetime.now().date()
    available_discounts = Discount.query.filter(
        and_(
            Discount.valid_from <= current_date,
            Discount.valid_to >= current_date
        )
    ).limit(5).all()  # Giới hạn chỉ hiển thị 5 mã
    
    return render_template('book_ride.html', 
                          user=current_user,
                          credit_cards=credit_cards,
                          wallets=wallets,
                          bank_accounts=bank_accounts,
                          discount_code=discount_code,
                          discount_percentage=discount_percentage,
                          max_discount=max_discount,
                          discount_applied=discount_applied,
                          available_discounts=available_discounts)

@book_ride_bp.route('/select-ride-type', methods=['GET'])
@login_required
def select_ride_type():
    return render_template('book_ride/ride_type_popup.html')

@book_ride_bp.route('/book-ride-shared', methods=['GET', 'POST'])
@login_required
def book_ride_shared():
    # Lấy thông tin phương thức thanh toán của user
    credit_cards = CreditCard.query.filter_by(user_id=current_user.user_id).all()
    wallets = Wallet.query.filter_by(user_id=current_user.user_id).all()
    bank_accounts = BankAccount.query.filter_by(user_id=current_user.user_id).all()
    
    return render_template('book_ride/book_ride_shared.html', 
                          user=current_user,
                          credit_cards=credit_cards,
                          wallets=wallets,
                          bank_accounts=bank_accounts)

@book_ride_bp.route('/book-ride-closed', methods=['GET', 'POST'])
@login_required
def book_ride_closed():
    # Lấy thông tin phương thức thanh toán của user
    credit_cards = CreditCard.query.filter_by(user_id=current_user.user_id).all()
    wallets = Wallet.query.filter_by(user_id=current_user.user_id).all()
    bank_accounts = BankAccount.query.filter_by(user_id=current_user.user_id).all()
    
    return render_template('book_ride/book_ride_closed.html', 
                          user=current_user,
                          credit_cards=credit_cards,
                          wallets=wallets,
                          bank_accounts=bank_accounts)