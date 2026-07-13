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


def staff_required(f):
    """
    Custom decorator to restrict access to approved guides (staff).
    Ensures the client is logged in, has role == 'staff', and status == 'approved'.
    Unauthenticated users are redirected to login, unauthorized users receive a 403.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'staff' or current_user.status != 'approved':
            # Return HTTP 403 Forbidden
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    """
    Custom decorator to restrict access to regular users (trekkers) only.
    Ensures the client is logged in and has role == 'user'.
    Unauthenticated users are redirected to login, unauthorized users receive a 403.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'user':
            # Return HTTP 403 Forbidden
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function


