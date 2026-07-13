from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models import Trek, Booking
from routes.utils import staff_required

staff = Blueprint('staff', __name__)

def is_trek_owner(trek):
    # Check if this trek belongs to the logged-in staff member
    return trek.assigned_staff_id == current_user.id


@staff.route('/dashboard')
@login_required
@staff_required
def staff_dashboard():
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date.asc()).all()

    trek_stats = []
    for trek in assigned_treks:
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
    trek_item = Trek.query.get_or_404(trek_id)

    # Ownership check
    if not is_trek_owner(trek_item):
        abort(403)

    if request.method == 'POST':
        status = request.form.get('status', '').strip()
        available_slots_str = request.form.get('available_slots', '').strip()

        if not status or not available_slots_str:
            flash("Please fill in all fields.", "danger")
            return render_template('staff/trek_detail.html', trek=trek_item)

        try:
            available_slots = int(available_slots_str)
            
            # Prevent available slots from exceeding total capacity minus bookings
            booked_count = Booking.query.filter_by(trek_id=trek_item.id, status='Booked').count()
            max_allowable_slots = trek_item.total_slots - booked_count

            if available_slots > max_allowable_slots:
                flash(f"Available slots cannot exceed remaining capacity. Maximum allowed: {max_allowable_slots}.", "danger")
                return render_template('staff/trek_detail.html', trek=trek_item)

            if available_slots < 0:
                flash("Available slots cannot be negative.", "danger")
                return render_template('staff/trek_detail.html', trek=trek_item)

            trek_item.status = status
            trek_item.available_slots = available_slots

            db.session.commit()
            flash(f"Trek details updated successfully.", "success")
            return redirect(url_for('staff.staff_dashboard'))

        except ValueError:
            flash("Available slots must be a valid integer.", "danger")
            return render_template('staff/trek_detail.html', trek=trek_item)
        except Exception:
            db.session.rollback()
            flash("An error occurred during update.", "danger")
            return render_template('staff/trek_detail.html', trek=trek_item)

    return render_template('staff/trek_detail.html', trek=trek_item)


@staff.route('/trek/<int:trek_id>/participants')
@login_required
@staff_required
def trek_participants(trek_id):
    trek_item = Trek.query.get_or_404(trek_id)

    # Ownership check
    if not is_trek_owner(trek_item):
        abort(403)

    bookings_list = Booking.query.filter_by(trek_id=trek_item.id).order_by(Booking.booking_date.desc()).all()
    return render_template('staff/participants.html', trek=trek_item, bookings=bookings_list)
