from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from extensions import db
from models import User, Trek, Booking
from routes.utils import admin_required

# Define the admin blueprint
admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    Administrator Dashboard view.
    Displays metrics like total treks, total clients (users+staff), and total bookings.
    """
    # Count total treks
    total_treks = Trek.query.count()
    
    # Count total users (trekkers) and staff (guides), excluding other admins
    total_users_staff = User.query.filter(User.role != 'admin').count()
    
    # Count total bookings
    total_bookings = Booking.query.count()

    return render_template(
        'admin/dashboard.html',
        total_treks=total_treks,
        total_users_staff=total_users_staff,
        total_bookings=total_bookings
    )


@admin.route('/treks')
@login_required
@admin_required
def manage_treks():
    """
    View to list all treks in a tabular format for administrative management.
    """
    treks_list = Trek.query.order_by(Trek.start_date.asc()).all()
    return render_template('admin/manage_treks.html', treks=treks_list)


@admin.route('/treks/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_trek():
    """
    Create a new trek in the system.
    """
    # Fetch all approved staff (guides) to allow assignment
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

        # Input validation
        if not name or not location or not difficulty or not duration_days or not total_slots or not start_date_str or not end_date_str:
            flash("Please fill in all required fields.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=None)

        try:
            # Parse date strings into Python date objects
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Type cast numeric inputs
            duration = int(duration_days)
            slots = int(total_slots)
            
            if duration <= 0 or slots <= 0:
                flash("Duration and slots must be positive numbers greater than zero.", "danger")
                return render_template('admin/trek_form.html', guides=guides, trek=None)
            
            # Staff assignment validation
            staff_id = int(assigned_staff_id) if assigned_staff_id else None
            
            # Create Trek instance (available_slots starts as total_slots)
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

        except ValueError as e:
            flash("Invalid input types. Please check your date and numeric values.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=None)
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while creating the trek.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=None)

    return render_template('admin/trek_form.html', guides=guides, trek=None)


@admin.route('/treks/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_trek(trek_id):
    """
    Edit details of an existing trek.
    """
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
                flash("Duration and slots must be positive numbers greater than zero.", "danger")
                return render_template('admin/trek_form.html', guides=guides, trek=trek_item)
            
            # Recalculate available slots based on booked slots count
            booked_slots = len([b for b in trek_item.bookings if b.status == 'Booked'])
            new_available_slots = new_total_slots - booked_slots
            
            if new_available_slots < 0:
                flash(f"Cannot reduce total slots to {new_total_slots} because {booked_slots} bookings already exist.", "danger")
                return render_template('admin/trek_form.html', guides=guides, trek=trek_item)

            staff_id = int(assigned_staff_id) if assigned_staff_id else None

            # Update trek properties
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

        except ValueError as e:
            flash("Invalid input types. Please verify dates and integers.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=trek_item)
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the trek.", "danger")
            return render_template('admin/trek_form.html', guides=guides, trek=trek_item)

    return render_template('admin/trek_form.html', guides=guides, trek=trek_item)


@admin.route('/treks/<int:trek_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_trek(trek_id):
    """
    Delete a trek from the system.
    Only triggered via POST requests from safe forms to prevent CSRF/unintended actions.
    """
    trek_item = Trek.query.get_or_404(trek_id)
    name = trek_item.name
    try:
        db.session.delete(trek_item)
        db.session.commit()
        flash(f"Trek '{name}' has been deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the trek.", "danger")
        
    return redirect(url_for('admin.manage_treks'))


@admin.route('/staff')
@login_required
@admin_required
def manage_staff():
    """
    View to list all staff (guides) and manage their approval statuses.
    """
    staff_list = User.query.filter_by(role='staff').order_by(User.created_at.desc()).all()
    return render_template('admin/manage_staff.html', staff_list=staff_list)


@admin.route('/staff/<int:staff_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_staff(staff_id):
    """
    Approve a guide's account registration to let them log in and be assigned to treks.
    """
    staff_member = User.query.filter_by(id=staff_id, role='staff').first_or_404()
    staff_member.status = 'approved'
    try:
        db.session.commit()
        flash(f"Guide '{staff_member.name}' registration has been approved successfully.", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred while approving the guide's account.", "danger")
    return redirect(url_for('admin.manage_staff'))


@admin.route('/staff/<int:staff_id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_staff(staff_id):
    """
    Blacklist a guide, preventing them from logging in or handling treks.
    """
    staff_member = User.query.filter_by(id=staff_id, role='staff').first_or_404()
    staff_member.status = 'blacklisted'
    try:
        db.session.commit()
        flash(f"Guide '{staff_member.name}' has been blacklisted and suspended.", "warning")
    except Exception:
        db.session.rollback()
        flash("An error occurred while blacklisting the guide's account.", "danger")
    return redirect(url_for('admin.manage_staff'))


@admin.route('/users')
@login_required
@admin_required
def manage_users():
    """
    View to list all platform users (trekkers) and manage their active statuses.
    """
    users_list = User.query.filter_by(role='user').order_by(User.created_at.desc()).all()
    return render_template('admin/manage_users.html', users_list=users_list)


@admin.route('/users/<int:user_id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_user(user_id):
    """
    Blacklist a trekker, terminating active sessions and preventing future log-ins.
    """
    user_member = User.query.filter_by(id=user_id, role='user').first_or_404()
    user_member.status = 'blacklisted'
    try:
        db.session.commit()
        flash(f"User '{user_member.name}' has been blacklisted and suspended.", "warning")
    except Exception:
        db.session.rollback()
        flash("An error occurred while blacklisting the user's account.", "danger")
    return redirect(url_for('admin.manage_users'))


@admin.route('/treks/<int:trek_id>/assign-staff', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_staff(trek_id):
    """
    Assign a guide (staff member) to lead a specific trek.
    Restricted to guides that are both approved and not blacklisted.
    """
    trek_item = Trek.query.get_or_404(trek_id)
    # Fetch approved and non-blacklisted staff members (guides)
    approved_staff = User.query.filter_by(role='staff', status='approved').order_by(User.name.asc()).all()

    if request.method == 'POST':
        staff_id_str = request.form.get('assigned_staff_id', '').strip()
        
        if not staff_id_str:
            trek_item.assigned_staff_id = None
        else:
            try:
                staff_id = int(staff_id_str)
                # Verify chosen staff member is valid and authorized
                staff_member = User.query.filter_by(id=staff_id, role='staff', status='approved').first()
                if not staff_member:
                    flash("Unauthorized or invalid guide selected.", "danger")
                    return render_template('admin/assign_staff.html', trek=trek_item, staff_list=approved_staff)
                
                trek_item.assigned_staff_id = staff_id
            except ValueError:
                flash("Invalid guide identifier.", "danger")
                return render_template('admin/assign_staff.html', trek=trek_item, staff_list=approved_staff)

        try:
            db.session.commit()
            flash(f"Guide assignment updated successfully for trek '{trek_item.name}'.", "success")
            return redirect(url_for('admin.manage_treks'))
        except Exception:
            db.session.rollback()
            flash("An error occurred while completing the guide assignment.", "danger")

    return render_template('admin/assign_staff.html', trek=trek_item, staff_list=approved_staff)


@admin.route('/search')
@login_required
@admin_required
def search():
    """
    Search platform entities (Treks, Guides, and Trekkers) by name using safe parameterized queries.
    Prevents SQL injection vulnerabilities.
    """
    query_str = request.args.get('q', '').strip()
    
    treks_results = []
    guides_results = []
    users_results = []

    if query_str:
        # Construct wildcards securely. SQLAlchemy's .like() compiles to safe placeholders.
        search_pattern = f"%{query_str}%"
        
        # Query matching treks
        treks_results = Trek.query.filter(Trek.name.like(search_pattern)).all()
        
        # Query matching guides (staff role)
        guides_results = User.query.filter(User.role == 'staff', User.name.like(search_pattern)).all()
        
        # Query matching trekkers (user role)
        users_results = User.query.filter(User.role == 'user', User.name.like(search_pattern)).all()

    return render_template(
        'admin/search_results.html',
        query=query_str,
        treks=treks_results,
        guides=guides_results,
        users=users_results
    )
