from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Trek, Booking

user = Blueprint('user', __name__)

def can_book(trek, user_obj):
    # Rule validation: check if booking is allowed
    if trek.status != 'Open':
        return False, "This trek is currently not open for bookings."

    if trek.available_slots <= 0:
        return False, "Sorry, this trek has no available slots remaining."

    # Check for duplicate active booking
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
def user_dashboard():
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    open_treks = Trek.query.filter_by(status='Open').order_by(Trek.start_date.asc()).limit(3).all()
    return render_template('user/dashboard.html', bookings=user_bookings, open_treks=open_treks)


@user.route('/treks')
@login_required
def list_treks():
    difficulty_filter = request.args.get('difficulty', '').strip()
    location_filter = request.args.get('location', '').strip()

    query = Trek.query.filter_by(status='Open')

    if difficulty_filter:
        query = query.filter(Trek.difficulty == difficulty_filter)

    if location_filter:
        query = query.filter(Trek.location.like(f"%{location_filter}%"))

    treks_list = query.order_by(Trek.start_date.asc()).all()

    return render_template(
        'user/treks.html',
        treks=treks_list,
        difficulty=difficulty_filter,
        location=location_filter
    )


@user.route('/trek/<int:trek_id>/book', methods=['POST'])
@login_required
def book_trek(trek_id):
    trek_item = Trek.query.get_or_404(trek_id)

    eligible, error_message = can_book(trek_item, current_user)
    if not eligible:
        flash(error_message, "danger")
        return redirect(url_for('user.list_treks'))

    try:
        # Book a slot and decrement available slots
        trek_item.available_slots -= 1
        
        new_booking = Booking(
            user_id=current_user.id,
            trek_id=trek_item.id,
            status='Booked'
        )

        db.session.add(new_booking)
        db.session.commit()
        
        flash(f"Slot on '{trek_item.name}' booked successfully.", "success")
        return redirect(url_for('user.user_dashboard'))
    except Exception:
        db.session.rollback()
        flash("An error occurred during booking.", "danger")
        return redirect(url_for('user.list_treks'))


@user.route('/bookings')
@login_required
def view_bookings():
    user_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return render_template('user/booking_history.html', bookings=user_bookings)


@user.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    # Ownership check
    if booking.user_id != current_user.id:
        abort(403)

    if booking.status != 'Booked':
        flash("This booking cannot be cancelled.", "danger")
        return redirect(url_for('user.view_bookings'))

    try:
        booking.status = 'Cancelled'
        
        # Increment slot count, but capped at total slots
        trek_item = booking.trek
        trek_item.available_slots = min(trek_item.available_slots + 1, trek_item.total_slots)

        db.session.commit()
        flash(f"Booking for '{trek_item.name}' has been cancelled.", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred during cancellation.", "danger")

    return redirect(url_for('user.view_bookings'))


@user.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact = request.form.get('contact', '').strip()

        if not name:
            flash("Name cannot be blank.", "danger")
            return render_template('user/profile.html')

        try:
            current_user.name = name
            current_user.contact = contact
            db.session.commit()
            
            flash("Profile updated successfully.", "success")
            return redirect(url_for('user.profile'))
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating profile.", "danger")
            return render_template('user/profile.html')

    return render_template('user/profile.html')
