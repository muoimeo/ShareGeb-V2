from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from src.models import db, User, Discount, CreditCard, Wallet, BankAccount
from datetime import datetime
from sqlalchemy import and_

book_ride_bp = Blueprint('book_ride', __name__)

@book_ride_bp.route('/book-ride', methods=['GET', 'POST'])
@login_required
def book_ride():
    """
    Route chính cho đặt xe, luôn chuyển hướng đến trang chọn loại xe.
    Đây là điểm đầu vào chung cho các loại chuyến đi.
    """
    # Log truy cập route
    current_app.logger.info(f"Accessing /book-ride route with method: {request.method}")
    current_app.logger.info(f"Query parameters: {request.args}")
    current_app.logger.info(f"Session data: {session}")
    
    # Kiểm tra param from_booking để quyết định chuyển hướng
    from_booking = request.args.get('from_booking')
    ride_type = request.args.get('ride_type')
    
    # Nếu có tham số from_booking và ride_type, chuyển hướng đến trang đặt xe tương ứng
    if from_booking == '1' and ride_type:
        # Tạo URL với tham số chứa thông tin điểm đón và điểm đến
        params = {}
        pickup = request.args.get('pickup')
        destination = request.args.get('destination')
        pickup_coords = request.args.get('pickup_coords')
        destination_coords = request.args.get('destination_coords')
        
        if pickup:
            params['pickup'] = pickup
        if destination:
            params['destination'] = destination
        if pickup_coords:
            params['pickup_coords'] = pickup_coords
        if destination_coords:
            params['destination_coords'] = destination_coords
        
        # Log chuyển hướng
        current_app.logger.info(f"Redirecting from /book-ride to /{ride_type} with params: {params}")
        
        # Chuyển về trang đặt xe ghép hoặc riêng dựa vào loại xe đã chọn
        if ride_type == 'closed':
            return redirect(url_for('book_ride.book_ride_closed', **params))
        else:
            return redirect(url_for('book_ride.book_ride_shared', **params))
    
    # Mặc định chuyển hướng đến trang chọn loại xe
    current_app.logger.info("Redirecting to select-ride-type page")
    return redirect(url_for('book_ride.select_ride_type'))

@book_ride_bp.route('/select-ride-type', methods=['GET'])
@login_required
def select_ride_type():
    return render_template('book_ride/ride_type_popup.html')

@book_ride_bp.route('/book-ride-shared', methods=['GET', 'POST'])
@login_required
def book_ride_shared():
    # Lưu thông tin ride_type vào session
    session['ride_type'] = 'shared'
    session['from_booking'] = '1'
    
    # Lưu thông tin điểm đón và điểm đến từ tham số URL vào session (nếu có)
    pickup = request.args.get('pickup')
    destination = request.args.get('destination')
    pickup_coords = request.args.get('pickup_coords')
    destination_coords = request.args.get('destination_coords')
    
    if pickup:
        session['pickup'] = pickup
    if destination:
        session['destination'] = destination
    if pickup_coords:
        session['pickup_coords'] = pickup_coords
    if destination_coords:
        session['destination_coords'] = destination_coords
    
    # Log thông tin session để debug
    current_app.logger.info(f"Book ride shared - Session data: {session}")
    
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
    # Lưu thông tin ride_type vào session
    session['ride_type'] = 'closed'
    session['from_booking'] = '1'
    
    # Lưu thông tin điểm đón và điểm đến từ tham số URL vào session (nếu có)
    pickup = request.args.get('pickup')
    destination = request.args.get('destination')
    pickup_coords = request.args.get('pickup_coords')
    destination_coords = request.args.get('destination_coords')
    
    if pickup:
        session['pickup'] = pickup
    if destination:
        session['destination'] = destination
    if pickup_coords:
        session['pickup_coords'] = pickup_coords
    if destination_coords:
        session['destination_coords'] = destination_coords
    
    # Log thông tin session để debug
    current_app.logger.info(f"Book ride closed - Session data: {session}")
    
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