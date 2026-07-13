from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User

# Define the authentication blueprint
auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    Allows users to register as either 'user' (trekker) or 'staff' (guide).
    Administrators cannot be created through this route.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        contact = request.form.get('contact', '').strip()
        role = request.form.get('role', '').strip()

        # Enforce basic validation
        if not name or not email or not password or not role:
            flash("All fields are required.", "danger")
            return render_template('auth/register.html')

        # Ensure registration is only for permitted roles
        if role not in ['user', 'staff']:
            flash("Invalid registration role.", "danger")
            return render_template('auth/register.html')

        # Check if email is already taken
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address is already registered.", "danger")
            return render_template('auth/register.html')

        # Set default statuses based on the role
        # Staff require admin approval (starts 'pending')
        # Trekkers are approved immediately (starts 'approved')
        status = 'pending' if role == 'staff' else 'approved'

        # Instantiate new User
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
                flash("Registration successful! Your staff account is pending administrator approval.", "info")
            else:
                flash("Registration successful! You can now log in.", "success")
                
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred during registration. Please try again.", "danger")
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user authentication (login).
    Verifies password hashes and checks account restrictions (pending approval / blacklisted).
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('auth/login.html')

        # Query user record from the database
        user_record = User.query.filter_by(email=email).first()

        # Validate credentials
        if not user_record or not user_record.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template('auth/login.html')

        # Rejection Rule 1: Account is blacklisted
        if user_record.status == 'blacklisted':
            flash("Your account has been suspended. Please contact support.", "danger")
            return render_template('auth/login.html')

        # Rejection Rule 2: Staff account is still pending administrator approval
        if user_record.role == 'staff' and user_record.status == 'pending':
            flash("Your guide account is pending admin approval. You cannot log in yet.", "info")
            return render_template('auth/login.html')

        # Authenticate user session
        login_user(user_record)
        
        flash(f"Welcome back, {user_record.name}!", "success")
        
        # Support redirecting to a previously requested URL (if login_required triggered it)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('index'))

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    """
    Handle session termination (logout).
    """
    logout_user()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('index'))
