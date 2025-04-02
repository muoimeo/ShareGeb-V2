from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.models import db, User
from flask_login import login_required, current_user

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile():
    return render_template('users/profile.html', user=current_user)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        user = current_user
        user.full_name = request.form.get('full_name')
        user.phone = request.form.get('phone')
        user.bio = request.form.get('bio')
        user.interests = request.form.get('interests')
        
        db.session.commit()
        flash('Thông tin đã được cập nhật thành công!', 'success')
        return redirect(url_for('profile.profile'))
    
    return render_template('users/edit_profile.html', user=current_user)

@profile_bp.route('/profile/settings')
@login_required
def settings():
    return render_template('users/settings.html', user=current_user) 