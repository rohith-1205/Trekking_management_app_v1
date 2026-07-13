from flask import Blueprint, jsonify, abort
from flask_login import login_required, current_user
from models import Trek, Booking, User

api = Blueprint('api', __name__)

@api.route('/treks', methods=['GET'])
def get_open_treks():
    # Public JSON list of open treks
    open_treks = Trek.query.filter_by(status='Open').order_by(Trek.start_date.asc()).all()
    serialized_treks = [trek.to_dict() for trek in open_treks]
    return jsonify(serialized_treks)


@api.route('/bookings/<int:user_id>', methods=['GET'])
@login_required
def get_user_bookings(user_id):
    # Retrieve user's bookings. Allowed for booking owner or admin.
    if current_user.id != user_id and current_user.role != 'admin':
        return jsonify({"error": "Forbidden"}), 403

    target_user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=target_user.id).order_by(Booking.booking_date.desc()).all()
    serialized_bookings = [booking.to_dict() for booking in bookings]
    return jsonify(serialized_bookings)
