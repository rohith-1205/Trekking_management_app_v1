from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        contact = request.form.get('contact', '').strip()
        role = request.form.get('role', '').strip()

        if not name or not email or not password or not role:
            flash("All fields are required.", "danger")
            return render_template('auth/register.html')

        if role not in ['user', 'staff']:
            flash("Invalid role choice.", "danger")
            return render_template('auth/register.html')

        # Check existing email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address is already registered.", "danger")
            return render_template('auth/register.html')

        # Guides start as pending, trekkers are approved immediately
        status = 'pending' if role == 'staff' else 'approved'

        new_user = User(
            name=name,
            email=email,
            role=role,
            status=status,
            contact=contact
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            
            if role == 'staff':
                flash("Registration successful! Guide account pending admin approval.", "info")
            else:
                flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('auth.login'))
        except Exception:
            db.session.rollback()
            flash("Error during registration. Please try again.", "danger")
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('auth/login.html')

        user_record = User.query.filter_by(email=email).first()

        if not user_record or not user_record.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template('auth/login.html')

        # Check blacklist
        if user_record.status == 'blacklisted':
            flash("Your account has been suspended.", "danger")
            return render_template('auth/login.html')

        # Check pending guides
        if user_record.role == 'staff' and user_record.status == 'pending':
            flash("Your account is pending admin approval.", "info")
            return render_template('auth/login.html')

        login_user(user_record)
        flash(f"Welcome, {user_record.name}!", "success")
        
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))
