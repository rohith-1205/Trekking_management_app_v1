from app import create_app
from extensions import db
from models import User

def seed_database():
    """
    Seeding script to initialize database tables and seed a default administrator account.
    Designed to be idempotent, so running it multiple times will not create duplicates.
    """
    # Create the app instance using our App Factory pattern
    app = create_app()

    # Enter the application context to access the database connection and configuration
    with app.app_context():
        print("[1/3] Initializing SQLite database and creating tables...")
        # db.create_all() creates all tables defined in models.py if they don't already exist
        db.create_all()
        
        # Fetch admin credentials from app configuration (which falls back to env variables)
        admin_email = app.config.get('ADMIN_EMAIL')
        admin_password = app.config.get('ADMIN_PASSWORD')
        
        print("[2/3] Checking if an administrator account already exists...")
        # Check if an admin exists by querying for users with the role 'admin'
        existing_admin = User.query.filter_by(role='admin').first()
        
        if not existing_admin:
            print(f"      No administrator found. Creating admin account: {admin_email}...")
            
            # Instantiate the default admin user
            admin_user = User(
                name="System Administrator",
                email=admin_email,
                role="admin",
                status="approved",  # Admin is pre-approved
                contact="9999999999"
            )
            # Hash the password securely using werkzeug.security inside the model's helper method
            admin_user.set_password(admin_password)
            
            # Save the new user to the session and commit it to the database
            db.session.add(admin_user)
            db.session.commit()
            print("[3/3] Administrator seeded successfully!")
        else:
            print(f"      Administrator already exists (Email: {existing_admin.email}). Skipping seeding.")

        print("Database initialization and seeding complete.")

if __name__ == '__main__':
    seed_database()
