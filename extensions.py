from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Create the database instance.
# We initialize it here without binding to any specific Flask app instance.
# This prevents circular dependency issues when different blueprints need to import 'db'.
db = SQLAlchemy()

# Create the login manager instance for managing user authentication and sessions.
login_manager = LoginManager()
# Configure the login view that login_required will redirect unauthorized users to.
# Since our auth blueprint has a stub for now, we point it to 'auth.login'.
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
