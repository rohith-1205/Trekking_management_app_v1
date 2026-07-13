import os
from flask import Flask, render_template, Blueprint
from config import Config
from extensions import db, login_manager
from models import User
from routes.auth_routes import auth as auth_bp
from routes.admin_routes import admin as admin_bp
from routes.staff_routes import staff as staff_bp
from routes.user_routes import user as user_bp
from routes.api_routes import api as api_bp


def create_app(config_class=Config):
    """
    App Factory function.
    Instead of hardcoding global 'app' instance, we define creation logic inside a function.
    This pattern is beneficial for testing and multiple configurations.
    """
    # Create the Flask application instance
    app = Flask(__name__)
    
    # Load configuration parameters from Config class
    app.config.from_object(config_class)

    # Ensure the instance folder exists (where SQLite database will reside)
    os.makedirs(app.instance_path, exist_ok=True)

    # Bind extensions (DB and Session/Login managers) to the application instance
    db.init_app(app)
    login_manager.init_app(app)

    # User loader for Flask-Login (fetches user from SQLite)
    @login_manager.user_loader
    def load_user(user_id):
        user_record = User.query.get(int(user_id))
        if user_record and user_record.status == 'blacklisted':
            return None
        return user_record

    # Register blueprints to categorize routes under separate URL scopes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Define a minimal root route that serves the welcome screen
    @app.route('/')
    def index():
        # Render the homepage template (which inherits from base.html)
        return render_template('index.html')

    # Automatically create SQLite database files & tables on startup if they do not exist
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    # This allows direct execution of 'python app.py' for quick debugging
    app = create_app()
    app.run(debug=True)
