from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model, UserMixin):
    """
    User Model representing platform users: Admins, Staff (Guides), and Users (Trekkers).
    Inherits from UserMixin to support Flask-Login's active user session management.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # User roles: 'admin', 'staff', 'user'
    role = db.Column(db.String(20), nullable=False, default='user')
    
    # User account registration status: 'pending', 'approved', 'blacklisted'
    status = db.Column(db.String(20), nullable=False, default='pending')
    
    contact = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    # A user (trekker) can have multiple bookings
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade="all, delete-orphan")
    
    # A staff member (guide) can be assigned to multiple treks
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy=True)

    def set_password(self, password):
        """
        Hashes the plain-text password using PBKDF2/SHA256 and stores it.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Checks the provided plain-text password against the stored hash.
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """
        Serializes user attributes to a standard Python dictionary.
        Excludes sensitive data like the password hash.
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'contact': self.contact,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Trek(db.Model):
    """
    Trek Model representing the hiking trips organized on the platform.
    """
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    
    # Difficulty levels: 'Easy', 'Moderate', 'Hard'
    difficulty = db.Column(db.String(20), nullable=False)
    
    duration_days = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    
    # Foreign key referencing User.id (specifically of role 'staff')
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Trek lifecycle status: 'Pending', 'Approved', 'Open', 'Closed', 'Completed'
    status = db.Column(db.String(20), nullable=False, default='Pending')
    
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # Relationships
    # A trek can have multiple bookings
    bookings = db.relationship('Booking', backref='trek', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """
        Serializes trek attributes to a standard Python dictionary.
        Converts dates to ISO formats for JSON compatibility.
        """
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'difficulty': self.difficulty,
            'duration_days': self.duration_days,
            'available_slots': self.available_slots,
            'total_slots': self.total_slots,
            'assigned_staff_id': self.assigned_staff_id,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }

    def __repr__(self):
        return f"<Trek {self.name} at {self.location}>"


class Booking(db.Model):
    """
    Booking Model representing a trekker booking a specific trek.
    """
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key links to User (Trekker)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Foreign key links to Trek
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    
    booking_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Booking status: 'Booked', 'Cancelled', 'Completed'
    status = db.Column(db.String(20), nullable=False, default='Booked')

    def to_dict(self):
        """
        Serializes booking attributes to a standard Python dictionary,
        including nested key-value pairs representing trek meta-information.
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'trek_id': self.trek_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'status': self.status,
            'trek': {
                'name': self.trek.name if self.trek else None,
                'location': self.trek.location if self.trek else None,
                'start_date': self.trek.start_date.isoformat() if self.trek and self.trek.start_date else None
            }
        }

    def __repr__(self):
        return f"<Booking {self.id} for User {self.user_id} on Trek {self.trek_id}>"
