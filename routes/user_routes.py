from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Trek, Booking
from routes.utils import user_required

# Define the user blueprint
user = Blueprint('user', __name__)

def can_book(trek, user_obj):
    """
    Helper function to evaluate if a user is eligible to book a specific trek.
    Returns: (is_eligible: bool, message: str)
    
    Checks in this specific order:
    1. Trek status is 'Open' (only active expeditions are joinable).
    2. Available slots > 0 (blocks overbooking).
    3. User does not have a duplicate active ('Booked') booking for the same trek.
    """
    # Check 1: Is the trek open for bookings?
    if trek.status != 'Open':
        return False, "This trek is currently not open for bookings."

    # Check 2: Are there remaining available slots?
    if trek.available_slots <= 0:
        return False, "Sorry, this trek has no available slots remaining."

    # Check 3: Does the user already have an active booking for this trek?
    duplicate_booking = Booking.query.filter_by(
        user_id=user_obj.id,
        trek_id=trek.id,
        status='Booked'
    ).first()
    
    if duplicate_booking:
        return False, "You have already booked a slot on this trek."

    return True, "Success"


@user.route('/dashboard')
@login_required
@user_required
def user_dashboard():
    """
    Trekker (User) Dashboard.
    Lists all bookings placed by the user and displays active available treks.
    """
    # Query all bookings made by the logged-in trekker
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    
    # Query active treks that the trekker might want to book
    open_treks = Trek.query.filter_by(status='Open').order_by(Trek.start_date.asc()).limit(3).all()

    return render_template('user/dashboard.html', bookings=user_bookings, open_treks=open_treks)


@user.route('/treks')
@login_required
@user_required
def list_treks():
    """
    Filterable and searchable catalog of open treks.
    Supports query parameters: 'difficulty' and 'location'.
    """
    difficulty_filter = request.args.get('difficulty', '').strip()
    location_filter = request.args.get('location', '').strip()

    # Start with a base query of treks that are open for bookings
    query = Trek.query.filter_by(status='Open')

    # Apply difficulty filter if specified
    if difficulty_filter:
        query = query.filter(Trek.difficulty == difficulty_filter)

    # Apply location search filter securely using case-insensitive LIKE pattern
    if location_filter:
        search_pattern = f"%{location_filter}%"
        query = query.filter(Trek.location.like(search_pattern))

    # Fetch results ordered by start date
    treks_list = query.order_by(Trek.start_date.asc()).all()

    # Fetch unique locations to populate a filter helper if needed (optional UX refinement)
    return render_template(
        'user/treks.html',
        treks=treks_list,
        difficulty=difficulty_filter,
        location=location_filter
    )


@user.route('/trek/<int:trek_id>/book', methods=['POST'])
@login_required
@user_required
def book_trek(trek_id):
    """
    Action endpoint to reserve a slot on a trek.
    Uses the can_book helper to validate request parameters safely.
    """
    trek_item = Trek.query.get_or_404(trek_id)

    # Validate booking eligibility using helper
    eligible, error_message = can_book(trek_item, current_user)
    
    if not eligible:
        flash(error_message, "danger")
        return redirect(url_for('user.list_treks'))

    try:
        # Decrement available slots on the trek
        trek_item.available_slots -= 1
        
        # Instantiate and save booking record
        new_booking = Booking(
            user_id=current_user.id,
            trek_id=trek_item.id,
            status='Booked'
        )

        db.session.add(new_booking)
        db.session.commit()
        
        flash(f"Success! Your slot on '{trek_item.name}' has been booked.", "success")
        return redirect(url_for('user.user_dashboard'))

    except Exception:
        db.session.rollback()
        flash("An error occurred while booking the trek. Please try again.", "danger")
        return redirect(url_for('user.list_treks'))


@user.route('/bookings')
@login_required
@user_required
def view_bookings():
    """
    Render full booking history for the current logged-in trekker.
    """
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('user/booking_history.html', bookings=user_bookings)


@user.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
@user_required
def cancel_booking(booking_id):
    """
    Cancel an active booking reservation.
    Updates the booking status to 'Cancelled' and increments available slots on the trek (+1).
    Restricted strictly to the booking owner.
    """
    booking = Booking.query.get_or_404(booking_id)

    # Ownership check: Ensure users can only cancel their own bookings
    if booking.user_id != current_user.id:
        abort(403)

    # State check: Only active bookings can be cancelled
    if booking.status != 'Booked':
        flash("This booking cannot be cancelled.", "danger")
        return redirect(url_for('user.view_bookings'))

    try:
        # Update booking status to Cancelled
        booking.status = 'Cancelled'
        
        # Restore available slot capacity (+1) on the associated trek
        # Uses min() to guarantee it never exceeds total_slots (overflow protection)
        trek_item = booking.trek
        trek_item.available_slots = min(trek_item.available_slots + 1, trek_item.total_slots)

        db.session.commit()
        flash(f"Your booking for '{trek_item.name}' has been cancelled.", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred while cancelling your booking.", "danger")

    return redirect(url_for('user.view_bookings'))


@user.route('/profile', methods=['GET', 'POST'])
@login_required
@user_required
def profile():
    """
    View and edit the trekker's personal profile (Name, Contact).
    Email and Role are read-only to enforce database integrity and security.
    """
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact = request.form.get('contact', '').strip()

        if not name:
            flash("Name field cannot be left blank.", "danger")
            return render_template('user/profile.html')

        try:
            current_user.name = name
            current_user.contact = contact
            db.session.commit()
            
            flash("Profile details updated successfully.", "success")
            return redirect(url_for('user.profile'))
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating your profile.", "danger")
            return render_template('user/profile.html')

    return render_template('user/profile.html')

