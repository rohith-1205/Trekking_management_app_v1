from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    """
    Custom decorator to restrict access to administrator-only views.
    Ensures the client is logged in and has role == 'admin'.
    If the user is not authenticated, they are redirected to the login page.
    If they are authenticated but lack the admin role, we return an HTTP 403 Forbidden error.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is authenticated
        if not current_user.is_authenticated:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        
        # Check if the user has the 'admin' role
        if current_user.role != 'admin':
            # Return HTTP 403 Forbidden
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function
