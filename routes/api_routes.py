from flask import Blueprint, jsonify, abort
from flask_login import login_required, current_user
from models import Trek, Booking, User

# Define the API blueprint
api = Blueprint('api', __name__)

@api.route('/treks', methods=['GET'])
def get_open_treks():
    """
    Public read-only API endpoint to fetch all active, open treks.
    Returns: JSON list of serialized trek items.
    """
    open_treks = Trek.query.filter_by(status='Open').order_by(Trek.start_date.asc()).all()
    # Serialize the list of SQLAlchemy model instances into plain dictionaries
    serialized_treks = [trek.to_dict() for trek in open_treks]
    return jsonify(serialized_treks)


@api.route('/bookings/<int:user_id>', methods=['GET'])
@login_required
def get_user_bookings(user_id):
    """
    Auth-protected API endpoint to retrieve the booking history of a specific user.
    Access is restricted to the booking owner themselves or an administrator.
    """
    # Verify authorization: current logged-in user must match target user_id, or be an admin
    if current_user.id != user_id and current_user.role != 'admin':
        # Return a clean HTTP 403 Forbidden JSON response instead of rendering a page
        return jsonify({"error": "Forbidden: You are not authorized to access this booking history."}), 403

    # Check if the requested user exists in the database
    target_user = User.query.get_or_404(user_id)

    # Query all booking records for the target user
    bookings = Booking.query.filter_by(user_id=target_user.id).order_by(Booking.booking_date.desc()).all()
    
    # Serialize model query results
    serialized_bookings = [booking.to_dict() for booking in bookings]
    return jsonify(serialized_bookings)
