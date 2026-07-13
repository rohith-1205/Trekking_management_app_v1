import os
from flask import Flask, render_template
from config import Config
from extensions import db, login_manager
from models import User
from routes.auth_routes import auth as auth_bp
from routes.admin_routes import admin as admin_bp
from routes.staff_routes import staff as staff_bp
from routes.user_routes import user as user_bp
from routes.api_routes import api as api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)

    # Init database and login manager
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # Fetch user from DB, block login if blacklisted
        user_record = User.query.get(int(user_id))
        if user_record and user_record.status == 'blacklisted':
            return None
        return user_record

    # Register all blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(api_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template('index.html')

    # Create tables automatically
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
