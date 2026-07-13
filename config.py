import os

# Define the base directory of the project for path construction
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Configuration class for Flask application.
    Contains basic settings such as secret key and database paths.
    """
    # Secret key for encrypting sessions and cookies
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-trekking-management-app-v1'
    
    # Database URI. By default, it points to 'instance/trekking.db' within our project root.
    # We construct the absolute path explicitly to ensure the database file is placed consistently.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'trekking.db')}"
    
    # Disable event tracking of Flask-SQLAlchemy to save overhead
    SQLALCHEMY_TRACK_MODIFICATIONS = False
