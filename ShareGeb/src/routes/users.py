import os
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, session, flash, make_response
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from src.models import db, User, BankAccount, Wallet
import secrets
import datetime
import time
import re
from werkzeug.security import generate_password_hash, check_password_hash

users_bp = Blueprint('users', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@users_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        if not email or not password:
            return render_template('users/log_in.html', error="Vui lòng điền đầy đủ email và mật khẩu")
        
        try:
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return render_template('users/log_in.html', error="Email hoặc mật khẩu không chính xác")
            
            if user.check_password(password):
                # Đăng nhập user bằng Flask-Login
                login_user(user, remember=True)
                
                # Lấy trang được yêu cầu trước đó
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('home.home'))
            else:
                return render_template('users/log_in.html', error="Email hoặc mật khẩu không chính xác")
        except Exception as e:
            print(f"Lỗi đăng nhập: {str(e)}")
            return render_template('users/log_in.html', error="Đã xảy ra lỗi khi đăng nhập. Vui lòng thử lại sau.")
    
    message = request.args.get('message')
    return render_template('users/log_in.html', message=message)

@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Sử dụng get() thay vì [] để tránh KeyError
        full_name = request.form.get('full_name', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        password = request.form.get('password', '')
        
        # Kiểm tra các trường bắt buộc
        if not all([full_name, email, phone, password]):
            return render_template('users/register.html', 
                                 error="Vui lòng điền đầy đủ thông tin",
                                 full_name=full_name, email=email, phone=phone)
        
        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('users/register.html', 
                                 error="Email đã được đăng ký",
                                 full_name=full_name, email=email, phone=phone)
        
        # Check if phone already exists
        existing_phone = User.query.filter_by(phone=phone).first()
        if existing_phone:
            return render_template('users/register.html', 
                                 error="Số điện thoại đã được đăng ký",
                                 full_name=full_name, email=email, phone=phone)
        
        # Validate password length
        if len(password.strip()) < 6:
            return render_template('users/register.html', 
                                 error="Mật khẩu phải có ít nhất 6 ký tự",
                                 full_name=full_name, email=email, phone=phone)
        
        # Create new user
        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            avatar='basic_avatar.png'  # Set default avatar explicitly
        )
        
        try:
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            
            print(f"Đăng ký thành công cho user: {email}")
            
            # Redirect to login page with success message
            return redirect(url_for('users.login', message="Đăng ký thành công! Vui lòng đăng nhập để tiếp tục."))
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi đăng ký: {str(e)}")
            return render_template('users/register.html', 
                                 error=f"Đăng ký thất bại: {str(e)}",
                                 full_name=full_name, email=email, phone=phone)
    
    return render_template('users/register.html')

@users_bp.route('/forget_password', methods=['GET', 'POST'], endpoint='forget_password')
def forget_password():
    if request.method == 'POST':
        email = request.form['email']
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return render_template('users/forget_password.html', error="Email not found")
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        try:
            db.session.commit()
            # In a real app, you would send an email with the reset link
            # For now, we'll just redirect to the reset page with the token
            return redirect(url_for('users.reset_password', token=token))
        except Exception as e:
            db.session.rollback()
            return render_template('users/forget_password.html', error=str(e))
            
    return render_template('users/forget_password.html')

@users_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Find user by token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or user.reset_token_expiry < datetime.datetime.now():
        return render_template('users/forget_password.html', error="Invalid or expired reset link")
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            return render_template('users/reset_password.html', error="Passwords do not match", token=token)
        
        try:
            # Update password with proper error handling
            if not password or len(password.strip()) < 6:
                return render_template('users/reset_password.html', error="Password must be at least 6 characters", token=token)
            
            # Set new password
            user.set_password(password.strip())
            user.reset_token = None
            user.reset_token_expiry = None
            
            # Commit changes
            db.session.commit()
            print(f"Password reset successful for user: {user.email}")
            
            return render_template('users/log_in.html', message="Password reset successful! Please login.")
        except Exception as e:
            db.session.rollback()
            print(f"Error resetting password: {str(e)}")
            return render_template('users/reset_password.html', error=f"Error resetting password: {str(e)}", token=token)
    
    return render_template('users/reset_password.html', token=token)

@users_bp.route('/logout')
@login_required
def logout():
    """Đăng xuất người dùng"""
    # Lưu trạng thái đăng nhập trước khi đăng xuất
    was_authenticated = current_user.is_authenticated
    
    # Đăng xuất người dùng bằng Flask-Login
    logout_user()
    
    # Xóa tất cả thông tin phiên làm việc
    session.clear()
    
    # Tạo response để chuyển hướng về trang đăng nhập
    response = make_response(redirect(url_for('users.login')))
    
    if was_authenticated:
        # Thêm cookie để đánh dấu trạng thái đăng xuất
        response.set_cookie('logged_out', 'true', max_age=30, path='/')
        
        # Xóa các cookie khác nếu cần
        for cookie_name in request.cookies:
            if cookie_name != 'session':
                response.delete_cookie(cookie_name, path='/')
    
    # Đảm bảo không lưu cache
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    
    # Thêm header tùy chỉnh để đánh dấu đã đăng xuất, hữu ích cho frontend
    response.headers['X-Logged-Out'] = 'true'
    
    # Hiển thị thông báo thành công
    flash('Bạn đã đăng xuất thành công!', 'success')
    
    return response

@users_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            # Xử lý upload ảnh đại diện
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and allowed_file(file.filename):
                    # Tạo tên file duy nhất
                    filename = secure_filename(file.filename)
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_filename = f"{timestamp}_{filename}"
                    
                    # Đảm bảo thư mục upload tồn tại
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'avatars')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Lưu file
                    file_path = os.path.join(upload_folder, unique_filename)
                    file.save(file_path)
                    
                    # Cập nhật avatar trong database
                    current_user.avatar = unique_filename
            
            # Cập nhật thông tin người dùng
            current_user.full_name = request.form.get('full_name')
            current_user.phone = request.form.get('phone')
            current_user.email = request.form.get('email')
            current_user.bio = request.form.get('bio')
            current_user.interests = request.form.get('interests')
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Cập nhật thông tin thành công',
                'user': {
                    'full_name': current_user.full_name,
                    'email': current_user.email,
                    'phone': current_user.phone,
                    'avatar': current_user.avatar
                }
            })
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating profile: {str(e)}')
            return jsonify({
                'success': False,
                'message': f'Có lỗi xảy ra khi cập nhật thông tin: {str(e)}'
            }), 500
    
    return render_template('users/profile.html', user=current_user, now=datetime.datetime.now())

@users_bp.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Chưa đăng nhập'})
        
    try:
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'message': 'Không có file được tải lên'})
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Không có file được chọn'})
        
        if file and allowed_file(file.filename):
            # Save file to avatars folder
            filename = secure_filename(file.filename)
            # Generate unique filename to avoid conflicts
            unique_filename = f"{session['user_id']}_{int(time.time())}_{filename}"
            
            # Directly use the Flask app's static folder
            avatar_dir = os.path.join(current_app.root_path, 'static', 'image', 'avatars')
            print(f"Avatar directory: {avatar_dir}")
            
            # Ensure directory exists
            os.makedirs(avatar_dir, exist_ok=True)
            
            # Save the file
            file_path = os.path.join(avatar_dir, unique_filename)
            print(f"Saving file to: {file_path}")
            file.save(file_path)
            print(f"File saved successfully")
            
            # Update user in database
            user = User.query.get(session['user_id'])
            if user:
                # Store the old avatar filename to delete it later if needed
                old_avatar = user.avatar
                print(f"Old avatar: {old_avatar}")
                
                try:
                    # Update user in database with explicit commit
                    user.avatar = unique_filename
                    db.session.commit()
                    print(f"User avatar updated in database to: {unique_filename}")
                    
                    # Force a refresh of the user object from the database to verify the update
                    db.session.refresh(user)
                    print(f"After refresh, user avatar is: {user.avatar}")
                    
                    # Update session data explicitly
                    session['avatar'] = unique_filename
                    print(f"Session avatar updated to: {unique_filename}")
                    
                    # Force session to be saved
                    session.modified = True
                    
                    return jsonify({'success': True, 'filename': unique_filename})
                except Exception as e:
                    db.session.rollback()
                    print(f"Database error: {str(e)}")
                    return jsonify({'success': False, 'message': f"Lỗi cơ sở dữ liệu: {str(e)}"})
            else:
                return jsonify({'success': False, 'message': 'Không tìm thấy người dùng'})
        else:
            return jsonify({'success': False, 'message': 'Loại file không hợp lệ'})
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error uploading avatar: {str(e)}")
        print(f"Traceback: {error_traceback}")
        return jsonify({'success': False, 'message': f"Lỗi: {str(e)}"})

@users_bp.route('/recent-rides')
def recent_rides():
    # Mock data for recent rides
    rides = [
        {
            'from': 'Hồ Hoàn Kiếm',
            'to': 'Văn Miếu',
            'date': '15/03/2024',
            'time': '14:30',
            'status': 'Hoàn thành',
            'rating': None
        },
        {
            'from': 'Hồ Tây',
            'to': 'Lotte Center',
            'date': '10/03/2024',
            'time': '09:15',
            'status': 'Hoàn thành',
            'rating': 5
        }
    ]
    return render_template('users/recent_rides.html', rides=rides)

@users_bp.route('/settings')
@login_required
def settings():
    now = datetime.datetime.now()
    return render_template('users/settings.html', now=now)

@users_bp.route('/add_bank_account', methods=['POST'])
@login_required
def add_bank_account():
    if request.method == 'POST':
        bank_name = request.form.get('bank_name')
        account_number = request.form.get('account_number')
        
        if not bank_name or not account_number:
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'})
        
        # Tạo tài khoản ngân hàng mới
        new_account = BankAccount(
            user_id=current_user.user_id,
            bank_name=bank_name,
            account_number=account_number,
            last_4_digits=account_number[-4:]
        )
        
        try:
            db.session.add(new_account)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Thêm tài khoản ngân hàng thành công'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Có lỗi xảy ra khi thêm tài khoản'})

@users_bp.route('/delete_bank_account/<int:account_id>', methods=['DELETE'])
@login_required
def delete_bank_account(account_id):
    account = BankAccount.query.get_or_404(account_id)
    
    # Kiểm tra xem tài khoản có thuộc về người dùng hiện tại không
    if account.user_id != current_user.user_id:
        return jsonify({'success': False, 'message': 'Không có quyền xóa tài khoản này'})
    
    try:
        db.session.delete(account)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Xóa tài khoản ngân hàng thành công'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra khi xóa tài khoản'})

@users_bp.route('/link_wallet', methods=['POST'])
@login_required
def link_wallet():
    if request.method == 'POST':
        wallet_type = request.form.get('wallet_type')
        balance = request.form.get('balance', 0.0)
        
        if not wallet_type:
            return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin'})
        
        # Tạo ví điện tử mới
        new_wallet = Wallet(
            user_id=current_user.user_id,
            balance=balance,
            currency='VND',
            status='active'
        )
        
        try:
            db.session.add(new_wallet)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Liên kết ví điện tử thành công'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Có lỗi xảy ra khi liên kết ví: {str(e)}'})

@users_bp.route('/api/bank-accounts')
@login_required
def get_bank_accounts():
    try:
        accounts = BankAccount.query.filter_by(user_id=current_user.user_id).all()
        accounts_data = []
        for account in accounts:
            accounts_data.append({
                'id': account.account_id,
                'bank_name': account.bank_name,
                'last_4_digits': account.last_4_digits
            })
        return jsonify({'success': True, 'accounts': accounts_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'accounts': []})

@users_bp.route('/api/wallets')
@login_required
def get_wallets():
    try:
        wallets = Wallet.query.filter_by(user_id=current_user.user_id).all()
        wallets_data = []
        for wallet in wallets:
            wallets_data.append({
                'id': wallet.wallet_id,
                'balance': float(wallet.balance),
                'currency': wallet.currency,
                'status': wallet.status
            })
        return jsonify({'success': True, 'wallets': wallets_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'wallets': []})

@users_bp.route('/check_login_status')
def check_login_status():
    """Kiểm tra trạng thái đăng nhập của người dùng"""
    # Đảm bảo không lưu cache
    response = jsonify({
        'is_authenticated': current_user.is_authenticated,
        'timestamp': datetime.now().timestamp()
    })
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response