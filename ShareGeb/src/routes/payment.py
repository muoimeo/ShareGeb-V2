from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from src.models import User, Payment, Transaction, CreditCard, BankAccount, Wallet, db
from datetime import datetime
import uuid
from flask import current_app
import random

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

@payment_bp.route('/wallet')
@login_required
def wallet():
    # Lấy thông tin ví của người dùng
    wallet = {
        'created_at': current_user.created_at,
        'last_transaction_at': None
    }
    
    # Lấy thông tin thẻ tín dụng
    credit_cards = CreditCard.query.filter_by(user_id=current_user.user_id).all()
    
    # Lấy thông tin tài khoản ngân hàng
    bank_accounts = BankAccount.query.filter_by(user_id=current_user.user_id).all()
    
    # Lấy lịch sử giao dịch
    transactions = Transaction.query.filter_by(user_id=current_user.user_id).order_by(Transaction.created_at.desc()).all()
    
    # Cập nhật thời gian giao dịch gần nhất
    if transactions and len(transactions) > 0:
        wallet['last_transaction_at'] = transactions[0].created_at
    
    return render_template('payments/wallet.html', user=current_user, wallet=wallet, 
                           transactions=transactions, credit_cards=credit_cards, bank_accounts=bank_accounts)

@payment_bp.route('/add_payment_method/<payment_type>')
@login_required
def add_payment_method(payment_type):
    now = datetime.now()
    valid_types = ['credit', 'bank', 'ewallet']
    
    # Log để debug
    current_app.logger.info(f"===== ADD PAYMENT METHOD DEBUG ======")
    current_app.logger.info(f"Payment type: {payment_type}")
    current_app.logger.info(f"Request args: {request.args}")
    current_app.logger.info(f"Request referrer: {request.referrer}")
    current_app.logger.info(f"Current session before processing: {dict(session)}") # Log session hiện tại

    if payment_type not in valid_types:
        flash('Phương thức thanh toán không hợp lệ', 'error')
        return redirect(url_for('users.settings'))

    # Xác định xem có phải đến từ trang đặt xe không
    from_booking = request.args.get('from_booking', '0')
    session['from_booking'] = from_booking # Luôn lưu trạng thái from_booking

    # Chỉ lưu thông tin chi tiết chuyến đi vào session nếu đến từ trang đặt xe
    if from_booking == '1':
        ride_type = request.args.get('ride_type')
        if ride_type:
            session['ride_type'] = ride_type
            current_app.logger.info(f"Đã lưu ride_type vào session từ args: {ride_type}")
        else:
            # Nếu from_booking=1 mà không có ride_type -> có lỗi logic ở trang trước
            current_app.logger.warning("from_booking=1 nhưng không có ride_type trong request.args!")
            # Có thể xóa ride_type cũ để tránh nhầm lẫn nếu cần
            # session.pop('ride_type', None)

        pickup = request.args.get('pickup')
        if pickup:
            session['pickup'] = pickup
            current_app.logger.info(f"Đã lưu pickup vào session từ args: {pickup}")

        destination = request.args.get('destination')
        if destination:
            session['destination'] = destination
            current_app.logger.info(f"Đã lưu destination vào session từ args: {destination}")

        pickup_coords = request.args.get('pickup_coords')
        if pickup_coords:
            session['pickup_coords'] = pickup_coords
            current_app.logger.info(f"Đã lưu pickup_coords vào session từ args: {pickup_coords}")

        destination_coords = request.args.get('destination_coords')
        if destination_coords:
            session['destination_coords'] = destination_coords
            current_app.logger.info(f"Đã lưu destination_coords vào session từ args: {destination_coords}")
    else:
        # Nếu không phải từ trang đặt xe, xóa thông tin chuyến đi cũ khỏi session để tránh nhầm lẫn
        session.pop('ride_type', None)
        session.pop('pickup', None)
        session.pop('destination', None)
        session.pop('pickup_coords', None)
        session.pop('destination_coords', None)
        current_app.logger.info("Không phải từ trang đặt xe, đã xóa thông tin chuyến đi cũ khỏi session (nếu có).")

    # Log session sau khi cập nhật
    current_app.logger.info(f"Session data after processing args: {dict(session)}")

    template = f'payments/add_{payment_type}.html'
    return render_template(template, now=now)

@payment_bp.route('/add_credit_card', methods=['POST'])
@login_required
def add_credit_card():
    try:
        card_type = request.form.get('card_type')
        card_number = request.form.get('card_number')
        expiry_month = request.form.get('expiry_month')
        expiry_year = request.form.get('expiry_year')
        card_holder = request.form.get('card_holder')
        cvv = request.form.get('cvv')
        
        # Thêm logging để debug
        current_app.logger.info("==== ADD CREDIT CARD FORM DATA ====")
        for key, value in request.form.items():
            current_app.logger.info(f"Form[{key}] = {value}")
        
        current_app.logger.info("==== ADD CREDIT CARD SESSION DATA ====")
        for key, value in session.items():
            current_app.logger.info(f"Session[{key}] = {value}")
        
        if not all([card_type, card_number, expiry_month, expiry_year, card_holder, cvv]):
            flash('Vui lòng điền đầy đủ thông tin thẻ', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='credit'))
        
        # Kiểm tra độ dài số thẻ
        if len(card_number) < 13 or len(card_number) > 16:
            flash('Số thẻ phải từ 13 đến 16 số', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='credit'))
        
        # Kiểm tra số thẻ chỉ chứa số
        if not card_number.isdigit():
            flash('Số thẻ chỉ được chứa số', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='credit'))
        
        # Tạo đối tượng datetime cho ngày hết hạn
        try:
            # Tạo datetime từ tháng và năm hết hạn
            expiry_date = datetime(int(expiry_year), int(expiry_month), 1)
        except ValueError:
            flash('Ngày hết hạn không hợp lệ', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='credit'))
        
        # Kiểm tra thẻ đã hết hạn chưa
        if expiry_date <= datetime.now():
            flash('Thẻ đã hết hạn', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='credit'))
        
        # Tạo object thẻ tín dụng mới
        card = CreditCard(
            user_id=current_user.user_id,
            card_type=card_type,
            card_number=card_number,
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            card_holder=card_holder,
            cvv=cvv,
            is_default=False
        )
        
        # Lưu vào database
        db.session.add(card)
        db.session.commit()
        
        flash('Thêm thẻ thành công', 'success')
        
        # Lấy thông tin đặt xe từ form
        from_booking = request.form.get('from_booking')
        ride_type = request.form.get('ride_type')
        pickup = request.form.get('pickup')
        destination = request.form.get('destination')
        pickup_coords = request.form.get('pickup_coords')
        destination_coords = request.form.get('destination_coords')
        
        # Log để debug
        current_app.logger.info(f"Form data: from_booking={from_booking}, ride_type={ride_type}, pickup={pickup}")
        
        # Chuyển hướng về trang trước đó
        if from_booking == '1':
            # Tạo URL với tham số chứa thông tin điểm đón và điểm đến
            params = {}
            if pickup:
                params['pickup'] = pickup
            if destination:
                params['destination'] = destination
            if pickup_coords:
                params['pickup_coords'] = pickup_coords
            if destination_coords:
                params['destination_coords'] = destination_coords
            
            # Log params trước khi chuyển hướng
            current_app.logger.info(f"Redirecting to {ride_type} ride with params: {params}")
            
            # Tạo URL để log
            if ride_type == 'closed':
                redirect_url = url_for('book_ride.book_ride_closed', **params)
            else:
                redirect_url = url_for('book_ride.book_ride_shared', **params)
                
            current_app.logger.info(f"Full redirect URL: {redirect_url}")
            
            # Chuyển về trang đặt xe ghép hoặc riêng dựa vào loại xe đã chọn
            if ride_type == 'closed':
                return redirect(url_for('book_ride.book_ride_closed', **params))
            else:
                return redirect(url_for('book_ride.book_ride_shared', **params))
        else:
            current_app.logger.info("Redirecting to profile page as from_booking is not '1'")
            return redirect(url_for('users.profile'))
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error adding credit card: {str(e)}')
        flash(f'Lỗi khi thêm thẻ: {str(e)}', 'error')
        return redirect(url_for('payment.add_payment_method', payment_type='credit'))

@payment_bp.route('/add_bank_account', methods=['POST'])
@login_required
def add_bank_account():
    try:
        bank_name = request.form.get('bank_name')
        account_number = request.form.get('account_number')
        account_holder = request.form.get('account_holder')
        
        # Thêm logging để debug
        current_app.logger.info("==== ADD BANK ACCOUNT FORM DATA ====")
        for key, value in request.form.items():
            current_app.logger.info(f"Form[{key}] = {value}")
        
        current_app.logger.info("==== ADD BANK ACCOUNT SESSION DATA ====")
        for key, value in session.items():
            current_app.logger.info(f"Session[{key}] = {value}")
        
        if not all([bank_name, account_number, account_holder]):
            flash('Vui lòng điền đầy đủ thông tin tài khoản ngân hàng', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='bank'))
        
        # Kiểm tra số tài khoản chỉ chứa số
        if not account_number.isdigit():
            flash('Số tài khoản chỉ được chứa số', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='bank'))
        
        # Tạo object tài khoản ngân hàng mới
        bank_account = BankAccount(
            user_id=current_user.user_id,
            bank_name=bank_name,
            account_number=account_number,
            account_holder=account_holder,
            branch="",  # Để trống vì không có trường branch trong form
            is_default=False
        )
        
        # Lưu vào database
        db.session.add(bank_account)
        db.session.commit()
        
        flash('Thêm tài khoản ngân hàng thành công', 'success')
        
        # Lấy thông tin đặt xe từ form
        from_booking = request.form.get('from_booking')
        ride_type = request.form.get('ride_type')
        pickup = request.form.get('pickup')
        destination = request.form.get('destination')
        pickup_coords = request.form.get('pickup_coords')
        destination_coords = request.form.get('destination_coords')
        
        # Log để debug
        current_app.logger.info(f"Form data: from_booking={from_booking}, ride_type={ride_type}, pickup={pickup}")
        
        # Chuyển hướng về trang trước đó
        if from_booking == '1':
            # Tạo URL với tham số chứa thông tin điểm đón và điểm đến
            params = {}
            if pickup:
                params['pickup'] = pickup
            if destination:
                params['destination'] = destination
            if pickup_coords:
                params['pickup_coords'] = pickup_coords
            if destination_coords:
                params['destination_coords'] = destination_coords
            
            # Log params trước khi chuyển hướng
            current_app.logger.info(f"Redirecting to {ride_type} ride with params: {params}")
            
            # Tạo URL để log
            if ride_type == 'closed':
                redirect_url = url_for('book_ride.book_ride_closed', **params)
            else:
                redirect_url = url_for('book_ride.book_ride_shared', **params)
                
            current_app.logger.info(f"Full redirect URL: {redirect_url}")
            
            # Chuyển về trang đặt xe ghép hoặc riêng dựa vào loại xe đã chọn
            if ride_type == 'closed':
                return redirect(url_for('book_ride.book_ride_closed', **params))
            else:
                return redirect(url_for('book_ride.book_ride_shared', **params))
        else:
            current_app.logger.info("Redirecting to profile page as from_booking is not '1'")
            return redirect(url_for('users.profile'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error adding bank account: {str(e)}')
        flash(f'Lỗi khi thêm tài khoản: {str(e)}', 'error')
        return redirect(url_for('payment.add_payment_method', payment_type='bank'))

@payment_bp.route('/add_ewallet', methods=['POST'])
@login_required
def add_ewallet():
    try:
        # Lấy thông tin ví điện tử từ form
        wallet_type = request.form.get('wallet_type')
        
        # Thêm logging của toàn bộ form data
        current_app.logger.info("==== ADD EWALLET FORM DATA ====")
        for key, value in request.form.items():
            current_app.logger.info(f"Form[{key}] = {value}")
        
        current_app.logger.info("==== ADD EWALLET SESSION DATA ====")
        for key, value in session.items():
            current_app.logger.info(f"Session[{key}] = {value}")
        
        # Kiểm tra thông tin
        if not wallet_type:
            flash('Vui lòng chọn loại ví điện tử', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='ewallet'))
        
        # Tạo số tài khoản ngẫu nhiên cho ví
        account_number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        
        # Tạo object ví điện tử mới
        wallet = Wallet(
            user_id=current_user.user_id,
            wallet_type=wallet_type,
            account_number=account_number,
            balance=0,
            currency='VND',
            status='active',
            is_default=False
        )
        
        # Lưu vào database
        db.session.add(wallet)
        db.session.commit()
        
        flash('Liên kết ví điện tử thành công', 'success')
        
        # Lấy thông tin đặt xe từ form
        from_booking = request.form.get('from_booking')
        ride_type = request.form.get('ride_type')
        pickup = request.form.get('pickup')
        destination = request.form.get('destination')
        pickup_coords = request.form.get('pickup_coords')
        destination_coords = request.form.get('destination_coords')
        
        # Log để debug
        current_app.logger.info(f"Form data: from_booking={from_booking}, ride_type={ride_type}, pickup={pickup}")
        
        # Chuyển hướng về trang trước đó
        if from_booking == '1':
            # Tạo URL với tham số chứa thông tin điểm đón và điểm đến
            params = {}
            if pickup:
                params['pickup'] = pickup
            if destination:
                params['destination'] = destination
            if pickup_coords:
                params['pickup_coords'] = pickup_coords
            if destination_coords:
                params['destination_coords'] = destination_coords
            
            # Log params trước khi chuyển hướng
            current_app.logger.info(f"Redirecting to {ride_type} ride with params: {params}")
            
            # Tạo URL để log
            if ride_type == 'closed':
                redirect_url = url_for('book_ride.book_ride_closed', **params)
            else:
                redirect_url = url_for('book_ride.book_ride_shared', **params)
                
            current_app.logger.info(f"Full redirect URL: {redirect_url}")
            
            # Chuyển về trang đặt xe ghép hoặc riêng dựa vào loại xe đã chọn
            if ride_type == 'closed':
                return redirect(url_for('book_ride.book_ride_closed', **params))
            else:
                return redirect(url_for('book_ride.book_ride_shared', **params))
        else:
            current_app.logger.info("Redirecting to profile page as from_booking is not '1'")
            return redirect(url_for('users.profile'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error adding wallet: {str(e)}')
        flash(f'Lỗi khi liên kết ví: {str(e)}', 'error')
        return redirect(url_for('payment.add_payment_method', payment_type='ewallet'))

@payment_bp.route('/topup_wallet', methods=['POST'])
@login_required
def topup_wallet():
    # Lấy thông tin từ request JSON
    data = request.get_json()
    amount = int(data.get('amount', 0))
    method = data.get('method', 'credit_card')
    card_id = data.get('card_id')
    
    # Kiểm tra số tiền
    if amount < 10000:
        return jsonify({'success': False, 'message': 'Số tiền nạp tối thiểu là 10,000đ'})
    
    # Xử lý nạp tiền
    try:
        # Tạo transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=current_user.user_id,
            amount=amount,
            type='deposit',
            status='completed',
            payment_method=method,
            description='Nạp tiền vào ví',
            created_at=datetime.now()
        )
        
        # Cập nhật số dư
        current_user.wallet_balance += amount
        
        # Lưu vào database
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Nạp tiền thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@payment_bp.route('/withdraw_wallet', methods=['POST'])
@login_required
def withdraw_wallet():
    # Lấy thông tin từ request JSON
    data = request.get_json()
    amount = int(data.get('amount', 0))
    method = data.get('method', 'bank_transfer')
    account_id = data.get('account_id')
    
    # Kiểm tra số tiền
    if amount < 10000:
        return jsonify({'success': False, 'message': 'Số tiền rút tối thiểu là 10,000đ'})
    
    if amount > current_user.wallet_balance:
        return jsonify({'success': False, 'message': 'Số dư không đủ'})
    
    # Xử lý rút tiền
    try:
        # Tạo transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=current_user.user_id,
            amount=amount,
            type='withdrawal',
            status='completed',
            payment_method=method,
            description='Rút tiền từ ví',
            created_at=datetime.now()
        )
        
        # Cập nhật số dư
        current_user.wallet_balance -= amount
        
        # Lưu vào database
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Rút tiền thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@payment_bp.route('/history')
@login_required
def transaction_history():
    # Lấy lịch sử giao dịch
    transactions = Transaction.query.filter_by(user_id=current_user.user_id).order_by(Transaction.created_at.desc()).all()
    return render_template('payments/history.html', transactions=transactions)

@payment_bp.route('/delete_bank_account/<int:account_id>', methods=['DELETE'])
@login_required
def delete_bank_account(account_id):
    try:
        account = BankAccount.query.filter_by(account_id=account_id, user_id=current_user.user_id).first()
        if not account:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy tài khoản'
            }), 404
        
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Xóa tài khoản thành công'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting bank account: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Lỗi khi xóa tài khoản: {str(e)}'
        }), 500

@payment_bp.route('/delete_credit_card/<int:card_id>', methods=['DELETE'])
@login_required
def delete_credit_card(card_id):
    try:
        card = CreditCard.query.filter_by(card_id=card_id, user_id=current_user.user_id).first()
        if not card:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy thẻ'
            }), 404
        
        db.session.delete(card)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Xóa thẻ thành công'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting credit card: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Lỗi khi xóa thẻ: {str(e)}'
        }), 500

@payment_bp.route('/delete_wallet/<int:wallet_id>', methods=['DELETE'])
@login_required
def delete_wallet(wallet_id):
    try:
        wallet = Wallet.query.filter_by(wallet_id=wallet_id, user_id=current_user.user_id).first()
        if not wallet:
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy ví'
            }), 404
        
        db.session.delete(wallet)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Xóa ví thành công'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting wallet: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Lỗi khi xóa ví: {str(e)}'
        }), 500

@payment_bp.route('/credit_cards')
@login_required
def get_credit_cards():
    try:
        cards = CreditCard.query.filter_by(user_id=current_user.user_id).all()
        cards_data = [{
            'id': card.card_id,
            'card_type': card.card_type,
            'last_4_digits': card.last_4_digits if hasattr(card, 'last_4_digits') else card.card_number[-4:]
        } for card in cards]
        return jsonify({'success': True, 'cards': cards_data})
    except Exception as e:
        current_app.logger.error(f'Error getting credit cards: {str(e)}')
        return jsonify({'success': False, 'message': 'Không thể tải thông tin thẻ tín dụng'}), 500

@payment_bp.route('/wallets')
@login_required
def get_wallets():
    try:
        wallets = Wallet.query.filter_by(user_id=current_user.user_id).all()
        wallets_data = [{
            'id': wallet.wallet_id,
            'wallet_type': wallet.wallet_type,
            'account_number': wallet.account_number,
            'last_4_digits': wallet.account_number[-4:]
        } for wallet in wallets]
        return jsonify({'success': True, 'wallets': wallets_data})
    except Exception as e:
        current_app.logger.error(f'Error getting wallets: {str(e)}')
        return jsonify({'success': False, 'message': 'Không thể tải thông tin ví điện tử'}), 500

@payment_bp.route('/bank_accounts')
@login_required
def get_bank_accounts():
    try:
        accounts = BankAccount.query.filter_by(user_id=current_user.user_id).all()
        accounts_data = [{
            'id': account.account_id,
            'bank_name': account.bank_name,
            'account_number': account.account_number,
            'last_4_digits': account.last_4_digits
        } for account in accounts]
        return jsonify({'success': True, 'accounts': accounts_data})
    except Exception as e:
        current_app.logger.error(f'Error getting bank accounts: {str(e)}')
        return jsonify({'success': False, 'message': 'Không thể tải thông tin tài khoản ngân hàng'}), 500