from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Trek, Booking
from routes.utils import staff_required

# Define the staff blueprint
staff = Blueprint('staff', __name__)

def is_trek_owner(trek):
    """
    Helper function to check if the current logged-in guide is assigned to lead the given trek.
    Returns True if current_user.id matches trek.assigned_staff_id, otherwise False.
    """
    return trek.assigned_staff_id == current_user.id


@staff.route('/dashboard')
@login_required
@staff_required
def staff_dashboard():
    """
    Trek Guide (Staff) Dashboard.
    Lists all treks assigned to the logged-in guide along with registered participant counts.
    """
    # Fetch treks assigned to this specific guide
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date.asc()).all()

    # Pre-calculate active booking counts for each trek to display on dashboard
    trek_stats = []
    for trek in assigned_treks:
        # Count bookings with status 'Booked' (excluding cancelled bookings)
        active_bookings_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        trek_stats.append({
            'trek': trek,
            'active_bookings_count': active_bookings_count
        })

    return render_template('staff/dashboard.html', trek_stats=trek_stats)


@staff.route('/trek/<int:trek_id>/update', methods=['GET', 'POST'])
@login_required
@staff_required
def update_trek(trek_id):
    """
    Allows a guide to update the available slots and status of a trek they are leading.
    Access is strictly restricted to the assigned guide via is_trek_owner(trek).
    """
    trek_item = Trek.query.get_or_404(trek_id)

    # Ownership enforcement check
    if not is_trek_owner(trek_item):
        # Return HTTP 403 Forbidden
        abort(403)

    if request.method == 'POST':
        status = request.form.get('status', '').strip()
        available_slots_str = request.form.get('available_slots', '').strip()

        if not status or not available_slots_str:
            flash("Please fill in all fields.", "danger")
            return render_template('staff/trek_detail.html', trek=trek_item)

        try:
            available_slots = int(available_slots_str)
            
            # Count active bookings to calculate remaining capacity
            booked_count = Booking.query.filter_by(trek_id=trek_item.id, status='Booked').count()
            max_allowable_slots = trek_item.total_slots - booked_count

            # Validation rules:
            # 1. Available slots cannot exceed remaining capacity (total_slots - booked_slots)
            if available_slots > max_allowable_slots:
                flash(f"Available slots cannot exceed remaining capacity. Maximum allowed: {max_allowable_slots} ({booked_count} slots already booked out of {trek_item.total_slots}).", "danger")
                return render_template('staff/trek_detail.html', trek=trek_item)

            # 2. Available slots cannot be negative
            if available_slots < 0:
                flash("Available slots cannot be negative.", "danger")
                return render_template('staff/trek_detail.html', trek=trek_item)

            # Update trek fields
            trek_item.status = status
            trek_item.available_slots = available_slots

            db.session.commit()
            flash(f"Trek '{trek_item.name}' status and slots updated successfully.", "success")
            return redirect(url_for('staff.staff_dashboard'))

        except ValueError:
            flash("Available slots must be an integer.", "danger")
            return render_template('staff/trek_detail.html', trek=trek_item)
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating the trek details.", "danger")
            return render_template('staff/trek_detail.html', trek=trek_item)

    return render_template('staff/trek_detail.html', trek=trek_item)


@staff.route('/trek/<int:trek_id>/participants')
@login_required
@staff_required
def trek_participants(trek_id):
    """
    Lists all trekkers who have registered for this specific trek.
    Access restricted to the assigned guide.
    """
    trek_item = Trek.query.get_or_404(trek_id)

    # Ownership enforcement check
    if not is_trek_owner(trek_item):
        abort(403)

    # Query active bookings (excluding cancelled bookings if desired, or displaying all status logs)
    bookings_list = Booking.query.filter_by(trek_id=trek_item.id).order_by(Booking.booking_date.desc()).all()

    return render_template('staff/participants.html', trek=trek_item, bookings=bookings_list)
