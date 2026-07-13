from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    # Restrict views to admins only
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    # Restrict views to approved staff guides only
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        if current_user.role != 'staff' or current_user.status != 'approved':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def user_required(f):
    # Restrict views to trekkers only
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        if current_user.role != 'user':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
