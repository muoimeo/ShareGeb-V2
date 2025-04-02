from flask import Blueprint, render_template, request

discounts_bp = Blueprint('discounts', __name__)

@discounts_bp.route('/discounts', methods=['GET', 'POST'])
def discounts():
    if request.method == 'POST':
        code = request.form['code']
        # Check code in database
        return render_template('discount/Voucher.html', message="Discount applied!")
    return render_template('discount/Voucher.html')