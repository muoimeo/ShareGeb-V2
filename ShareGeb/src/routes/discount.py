from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from src.models import db, Discount, DiscountUsage, User
from datetime import datetime
from sqlalchemy import and_

discount_bp = Blueprint('discount', __name__)

@discount_bp.route('/vouchers', methods=['GET'])
def voucher_list():
    """Hiển thị danh sách mã giảm giá của người dùng"""
    if 'user_id' not in session:
        return redirect(url_for('users.login'))
    
    # Lấy các mã giảm giá hiện có
    current_date = datetime.now().date()
    available_discounts = Discount.query.filter(
        and_(
            Discount.valid_from <= current_date,
            Discount.valid_to >= current_date
        )
    ).all()
    
    # Lấy các mã giảm giá đã dùng
    user_id = session.get('user_id')
    used_discounts = db.session.query(DiscountUsage)\
        .join(Discount)\
        .filter(DiscountUsage.ride_passenger.has(user_id=user_id))\
        .all()
    
    return render_template('discount/Voucher.html', 
                           available_discounts=available_discounts, 
                           used_discounts=used_discounts)

@discount_bp.route('/vouchers/apply', methods=['POST'])
def apply_discount():
    """Áp dụng mã giảm giá vào phiên hiện tại"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập để áp dụng mã giảm giá'})
    
    code = request.form.get('code')
    if not code:
        return render_template('discount/Voucher.html', 
                               message='Vui lòng nhập mã giảm giá', 
                               success=False)
    
    # Kiểm tra mã giảm giá
    current_date = datetime.now().date()
    discount = Discount.query.filter(
        and_(
            Discount.code == code,
            Discount.valid_from <= current_date,
            Discount.valid_to >= current_date
        )
    ).first()
    
    if not discount:
        return render_template('discount/Voucher.html', 
                               message='Mã giảm giá không tồn tại hoặc đã hết hạn', 
                               success=False)
    
    # Kiểm tra số lần sử dụng
    usage_count = DiscountUsage.query.filter_by(discount_id=discount.id).count()
    
    if usage_count >= discount.max_usage:
        return render_template('discount/Voucher.html', 
                               message='Mã giảm giá đã hết lượt sử dụng', 
                               success=False)
    
    # Lưu thông tin mã giảm giá vào session
    session['discount_code'] = discount.code
    session['discount_percentage'] = float(discount.discount_percentage)
    session['discount_max_amount'] = float(discount.max_discount_amount)
    session['discount_id'] = discount.id
    session.modified = True
    
    # Chuyển hướng đến trang voucher với thông báo thành công
    return render_template('discount/Voucher.html', 
                           message=f'Đã áp dụng mã giảm giá {discount.code}', 
                           success=True)

@discount_bp.route('/api/validate-discount', methods=['POST'])
def validate_discount():
    """API để xác thực mã giảm giá"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập để áp dụng mã giảm giá'})
    
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({'success': False, 'message': 'Vui lòng nhập mã giảm giá'})
    
    # Kiểm tra mã giảm giá
    current_date = datetime.now().date()
    discount = Discount.query.filter(
        and_(
            Discount.code == code,
            Discount.valid_from <= current_date,
            Discount.valid_to >= current_date
        )
    ).first()
    
    if not discount:
        return jsonify({'success': False, 'message': 'Mã giảm giá không tồn tại hoặc đã hết hạn'})
    
    # Kiểm tra số lần sử dụng
    usage_count = DiscountUsage.query.filter_by(discount_id=discount.id).count()
    
    if usage_count >= discount.max_usage:
        return jsonify({'success': False, 'message': 'Mã giảm giá đã hết lượt sử dụng'})
    
    # Lưu thông tin mã giảm giá vào session
    session['discount_code'] = discount.code
    session['discount_percentage'] = float(discount.discount_percentage)
    session['discount_max_amount'] = float(discount.max_discount_amount)
    session['discount_id'] = discount.id
    session.modified = True
    
    return jsonify({
        'success': True, 
        'message': 'Mã giảm giá hợp lệ',
        'discount_percentage': float(discount.discount_percentage),
        'max_discount_amount': float(discount.max_discount_amount),
        'code': discount.code
    }) 