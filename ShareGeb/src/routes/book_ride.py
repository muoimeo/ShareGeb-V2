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
        
        return redirect(url_for('book_ride.select_ride_type'))
    
    # Chuyển hướng đến trang chọn loại xe
    return redirect(url_for('book_ride.select_ride_type'))

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
    
    # Chuẩn bị dữ liệu để truyền đến template
    template_data = {
        'user': current_user,
        'credit_cards': credit_cards,
        'wallets': wallets,
        'bank_accounts': bank_accounts
    }
    
    # Lấy thông tin điểm đón và điểm đến từ tham số URL (nếu có)
    pickup = request.args.get('pickup')
    destination = request.args.get('destination')
    pickup_coords = request.args.get('pickup_coords')
    destination_coords = request.args.get('destination_coords')
    
    if pickup:
        template_data['pickup'] = pickup
    if destination:
        template_data['destination'] = destination
    if pickup_coords:
        template_data['pickup_coords'] = pickup_coords
    if destination_coords:
        template_data['destination_coords'] = destination_coords
    
    return render_template('book_ride/book_ride_shared.html', **template_data)

@book_ride_bp.route('/book-ride-closed', methods=['GET', 'POST'])
@login_required
def book_ride_closed():
    # Lấy thông tin phương thức thanh toán của user
    credit_cards = CreditCard.query.filter_by(user_id=current_user.user_id).all()
    wallets = Wallet.query.filter_by(user_id=current_user.user_id).all()
    bank_accounts = BankAccount.query.filter_by(user_id=current_user.user_id).all()
    
    # Chuẩn bị dữ liệu để truyền đến template
    template_data = {
        'user': current_user,
        'credit_cards': credit_cards,
        'wallets': wallets,
        'bank_accounts': bank_accounts
    }
    
    # Lấy thông tin điểm đón và điểm đến từ tham số URL (nếu có)
    pickup = request.args.get('pickup')
    destination = request.args.get('destination')
    pickup_coords = request.args.get('pickup_coords')
    destination_coords = request.args.get('destination_coords')
    
    if pickup:
        template_data['pickup'] = pickup
    if destination:
        template_data['destination'] = destination
    if pickup_coords:
        template_data['pickup_coords'] = pickup_coords
    if destination_coords:
        template_data['destination_coords'] = destination_coords
    
    return render_template('book_ride/book_ride_closed.html', **template_data)