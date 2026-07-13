from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from extensions import db
from models import User, Trek, Booking
from routes.utils import admin_required

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    total_treks = Trek.query.count()
    total_users_staff = User.query.filter(User.role != 'admin').count()
    total_bookings = Booking.query.count()

    # Query bookings per trek for stats visualization
    chart_labels = []
    chart_data = []
    
    all_treks = Trek.query.order_by(Trek.start_date.asc()).all()
    for trek in all_treks:
        chart_labels.append(trek.name)
        active_bookings_count = Booking.query.filter_by(trek_id=trek.id, status='Booked').count()
        chart_data.append(active_bookings_count)

    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users_staff=total_users_staff,
        total_bookings=total_bookings,
        chart_labels=chart_labels,
        chart_data=chart_data
    )


@admin.route('/treks')
@login_required
@admin_required
def manage_treks():
    treks_list = Trek.query.order_by(Trek.start_date.asc()).all()
    return render_template('admin/manage_treks.html', treks=treks_list)


@admin.route('/treks/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_trek():
    guides = User.query.filter_by(role='staff', status='approved').all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        duration_days = request.form.get('duration_days', '').strip()
        total_slots = request.form.get('total_slots', '').strip()
        assigned_staff_id = request.form.get('assigned_staff_id', '').strip()
        status = request.form.get('status', 'Pending').strip()
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()

        if not name or not location or not difficulty or not duration_days or not total_slots or not start_date_str or not end_date_str:
            flash("Please fill in all required fields.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=None)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            duration = int(duration_days)
            slots = int(total_slots)
            
            if duration <= 0 or slots <= 0:
                flash("Duration and slots must be positive numbers.", "danger")
                return render_template('admin/trek_form.html', guides=guides, trek=None)
            
            staff_id = int(assigned_staff_id) if assigned_staff_id else None
            
            new_trek = Trek(
                name=name,
                location=location,
                difficulty=difficulty,
                duration_days=duration,
                total_slots=slots,
                available_slots=slots,
                assigned_staff_id=staff_id,
                status=status,
                start_date=start_date,
                end_date=end_date
            )

            db.session.add(new_trek)
            db.session.commit()
            flash(f"Trek '{name}' created successfully!", "success")
            return redirect(url_for('admin.manage_treks'))

        except ValueError:
            flash("Invalid inputs. Please verify format.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=None)
        except Exception:
            db.session.rollback()
            flash("An error occurred while creating the trek.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=None)

    return render_template('admin/trek_form.html', guides=guides, trek=None)


@admin.route('/treks/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trek(trek_id):
    trek_item = Trek.query.get_or_404(trek_id)
    guides = User.query.filter_by(role='staff', status='approved').all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        location = request.form.get('location', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        duration_days = request.form.get('duration_days', '').strip()
        total_slots = request.form.get('total_slots', '').strip()
        assigned_staff_id = request.form.get('assigned_staff_id', '').strip()
        status = request.form.get('status', '').strip()
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()

        if not name or not location or not difficulty or not duration_days or not total_slots or not start_date_str or not end_date_str or not status:
            flash("Please fill in all required fields.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=trek_item)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            duration = int(duration_days)
            new_total_slots = int(total_slots)
            
            if duration <= 0 or new_total_slots <= 0:
                flash("Duration and slots must be positive numbers.", "danger")
                return render_template('admin/trek_form.html', guides=guides, trek=trek_item)
            
            booked_slots = len([b for b in trek_item.bookings if b.status == 'Booked'])
            new_available_slots = new_total_slots - booked_slots
            
            if new_available_slots < 0:
                flash(f"Cannot reduce total slots to {new_total_slots} because {booked_slots} bookings already exist.", "danger")
                return render_template('admin/trek_form.html', guides=guides, trek=trek_item)

            staff_id = int(assigned_staff_id) if assigned_staff_id else None

            trek_item.name = name
            trek_item.location = location
            trek_item.difficulty = difficulty
            trek_item.duration_days = duration
            trek_item.total_slots = new_total_slots
            trek_item.available_slots = new_available_slots
            trek_item.assigned_staff_id = staff_id
            trek_item.status = status
            trek_item.start_date = start_date
            trek_item.end_date = end_date

            db.session.commit()
            flash(f"Trek '{name}' updated successfully!", "success")
            return redirect(url_for('admin.manage_treks'))

        except ValueError:
            flash("Invalid input formats.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=trek_item)
        except Exception:
            db.session.rollback()
            flash("An error occurred while updating the trek.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=trek_item)

    return render_template('admin/trek_form.html', guides=guides, trek=trek_item)


@admin.route('/treks/<int:trek_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_trek(trek_id):
    trek_item = Trek.query.get_or_404(trek_id)
    name = trek_item.name
    try:
        db.session.delete(trek_item)
        db.session.commit()
        flash(f"Trek '{name}' has been deleted.", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred while deleting the trek.", "danger")
        
    return redirect(url_for('admin.manage_treks'))


@admin.route('/staff')
@login_required
@admin_required
def manage_staff():
    staff_list = User.query.filter_by(role='staff').order_by(User.created_at.desc()).all()
    return render_template('admin/manage_staff.html', staff_list=staff_list)


@admin.route('/staff/<int:staff_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_staff(staff_id):
    staff_member = User.query.filter_by(id=staff_id, role='staff').first_or_404()
    staff_member.status = 'approved'
    try:
        db.session.commit()
        flash(f"Guide '{staff_member.name}' registration approved.", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred during approval.", "danger")
    return redirect(url_for('admin.manage_staff'))


@admin.route('/staff/<int:staff_id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_staff(staff_id):
    staff_member = User.query.filter_by(id=staff_id, role='staff').first_or_404()
    staff_member.status = 'blacklisted'
    try:
        db.session.commit()
        flash(f"Guide '{staff_member.name}' has been blacklisted.", "warning")
    except Exception:
        db.session.rollback()
        flash("An error occurred.", "danger")
    return redirect(url_for('admin.manage_staff'))


@admin.route('/users')
@login_required
@admin_required
def manage_users():
    users_list = User.query.filter_by(role='user').order_by(User.created_at.desc()).all()
    return render_template('admin/manage_users.html', users_list=users_list)


@admin.route('/users/<int:user_id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_user(user_id):
    user_member = User.query.filter_by(id=user_id, role='user').first_or_404()
    user_member.status = 'blacklisted'
    try:
        db.session.commit()
        flash(f"User '{user_member.name}' has been blacklisted.", "warning")
    except Exception:
        db.session.rollback()
        flash("An error occurred.", "danger")
    return redirect(url_for('admin.manage_users'))


@admin.route('/treks/<int:trek_id>/assign-staff', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_staff(trek_id):
    trek_item = Trek.query.get_or_404(trek_id)
    approved_staff = User.query.filter_by(role='staff', status='approved').order_by(User.name.asc()).all()

    if request.method == 'POST':
        staff_id_str = request.form.get('assigned_staff_id', '').strip()
        
        if not staff_id_str:
            trek_item.assigned_staff_id = None
        else:
            try:
                staff_id = int(staff_id_str)
                staff_member = User.query.filter_by(id=staff_id, role='staff', status='approved').first()
                if not staff_member:
                    flash("Invalid guide selected.", "danger")
                    return render_template('admin/assign_staff.html', trek=trek_item, staff_list=approved_staff)
                
                trek_item.assigned_staff_id = staff_id
            except ValueError:
                flash("Invalid guide identifier.", "danger")
                return render_template('admin/assign_staff.html', trek=trek_item, staff_list=approved_staff)

        try:
            db.session.commit()
            flash(f"Guide assignment updated successfully.", "success")
            return redirect(url_for('admin.manage_treks'))
        except Exception:
            db.session.rollback()
            flash("An error occurred while saving guide assignment.", "danger")

    return render_template('admin/assign_staff.html', trek=trek_item, staff_list=approved_staff)


@admin.route('/search')
@login_required
@admin_required
def search():
    query_str = request.args.get('q', '').strip()
    
    treks_results = []
    guides_results = []
    users_results = []

    if query_str:
        search_pattern = f"%{query_str}%"
        
        treks_results = Trek.query.filter(Trek.name.like(search_pattern)).all()
        guides_results = User.query.filter(User.role == 'staff', User.name.like(search_pattern)).all()
        users_results = User.query.filter(User.role == 'user', User.name.like(search_pattern)).all()

    return render_template(
        'admin/search_results.html',
        query=query_str,
        treks=treks_results,
        guides=guides_results,
        users=users_results
    )
