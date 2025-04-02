from flask import Blueprint, render_template, request

cancel_ride_bp = Blueprint('cancel_ride', __name__)

@cancel_ride_bp.route('/cancel_ride', methods=['GET', 'POST'])
def cancel_ride():
    if request.method == 'POST':
        ride_id = request.form['ride_id']
        # Add logic to delete from database
        return render_template('book_ride/cancel_ride.html', message="Ride canceled!")
    return render_template('book_ride/cancel_ride.html')