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
    
    if payment_type not in valid_types:
        flash('Phương thức thanh toán không hợp lệ', 'error')
        return redirect(url_for('users.settings'))
    
    # Lưu đường dẫn trước đó để chuyển hướng sau khi thêm
    from_booking = request.args.get('from_booking', '0')
    session['from_booking'] = from_booking
    
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
            expiry_date = datetime.strptime(f"{expiry_year}-{expiry_month}-01", "%y-%m-%d").date()
            
            # Kiểm tra thẻ không được hết hạn
            if expiry_date < datetime.now().date():
                flash('Thẻ đã hết hạn', 'error')
                return redirect(url_for('payment.add_payment_method', payment_type='credit'))
        except ValueError:
            flash('Ngày hết hạn không hợp lệ', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='credit'))
        
        # Tạo object thẻ mới
        card = CreditCard(
            user_id=current_user.user_id,
            card_number=card_number,
            expiry_date=expiry_date,
            card_holder_name=card_holder,
            card_type=card_type
        )
        
        # Lưu vào database
        db.session.add(card)
        db.session.commit()
        
        flash('Thêm thẻ thành công', 'success')
        
        # Chuyển hướng về trang trước đó
        if session.get('from_booking') == '1':
            return redirect(url_for('book_ride.book_ride'))
        else:
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
        
        if not all([bank_name, account_number, account_holder]):
            flash('Vui lòng điền đầy đủ thông tin tài khoản', 'error')
            return redirect(url_for('payment.add_payment_method', payment_type='bank'))
        
        # Tạo object tài khoản mới
        account = BankAccount(
            user_id=current_user.user_id,
            bank_name=bank_name,
            account_number=account_number,
            account_holder_name=account_holder
        )
        
        # Lưu vào database
        db.session.add(account)
        db.session.commit()
        
        flash('Thêm tài khoản thành công', 'success')
        
        # Chuyển hướng về trang trước đó
        if session.get('from_booking') == '1':
            return redirect(url_for('book_ride.book_ride'))
        else:
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
        
        # Chuyển hướng về trang trước đó
        if session.get('from_booking') == '1':
            return redirect(url_for('book_ride.book_ride'))
        else:
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