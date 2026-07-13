# Project Report: TrekVoyage Trekking Management App V1

## 1. Executive Summary
TrekVoyage is a role-based, modular, and premium web application built using the Flask micro-framework. It is designed to manage outdoor trekking expeditions, staff (guides), and users (trekkers). The system enforces strict role-based access control (RBAC), prevents security exploits like SQL Injection and IDOR, and integrates real-time visualization dashboards.

---

## 2. Technology Stack
* **Backend**: Flask 3.x, Jinja2 template engine
* **Database**: SQLite (managed programmatically via Flask-SQLAlchemy)
* **Frontend styling**: Bootstrap 5 (linked via CDN) & customized CSS stylesheet
* **Visualizations**: Chart.js (CDN-based interactive stats bar charts)
* **Security & Auth**: Flask-Login, Werkzeug Security

---

## 3. Directory Layout
```text
trekking_app/
├── app.py                   # Flask App Factory (create_app)
├── config.py                # Database and session configuration
├── extensions.py            # Global DB & Login manager instances
├── models.py                # Database models (User, Trek, Booking)
├── seed.py                  # Database initialization & admin seeder
├── requirements.txt         # Project dependency list
├── routes/                  # Controller blueprinted layers
│   ├── auth_routes.py       # User authentication flows
│   ├── admin_routes.py      # Admin panels & CRUD operations
│   ├── staff_routes.py      # Guide dash & slot controls
│   ├── user_routes.py       # Trekker bookings & profile settings
│   ├── api_routes.py        # Read-only REST JSON API endpoints
│   └── utils.py             # Custom authorization decorators
├── static/
│   └── css/
│       └── style.css        # Custom theme style sheet (Teal & Orange)
└── templates/               # Jinja2 templates folder
    ├── base.html            # Main base layout layout
    ├── index.html           # Landing page Welcome screen
    ├── auth/                # Register / Login forms
    ├── admin/               # Admin views & trek forms
    ├── staff/               # Staff portal views
    └── user/                # User dashboard & booking history
```

---

## 4. Database Schema
The database uses three interconnected relational tables mapping foreign key constraints:

### 4.1. User Table (`users`)
* `id` (INTEGER, Primary Key)
* `name` (VARCHAR, Not Null)
* `email` (VARCHAR, Unique, Indexed, Not Null)
* `password_hash` (VARCHAR, Not Null)
* `role` (VARCHAR, `'admin'`, `'staff'`, or `'user'`)
* `status` (VARCHAR, `'pending'`, `'approved'`, or `'blacklisted'`)
* `contact` (VARCHAR)
* `created_at` (DATETIME)

### 4.2. Trek Table (`treks`)
* `id` (INTEGER, Primary Key)
* `name` (VARCHAR, Not Null)
* `location` (VARCHAR, Not Null)
* `difficulty` (VARCHAR, `'Easy'`, `'Moderate'`, `'Hard'`)
* `duration_days` (INTEGER)
* `available_slots` (INTEGER)
* `total_slots` (INTEGER)
* `assigned_staff_id` (INTEGER, Foreign Key referencing `users.id`)
* `status` (VARCHAR, `'Pending'`, `'Approved'`, `'Open'`, `'Closed'`, `'Completed'`)
* `start_date` (DATE)
* `end_date` (DATE)

### 4.3. Booking Table (`bookings`)
* `id` (INTEGER, Primary Key)
* `user_id` (INTEGER, Foreign Key referencing `users.id`)
* `trek_id` (INTEGER, Foreign Key referencing `treks.id`)
* `booking_date` (DATETIME)
* `status` (VARCHAR, `'Booked'`, `'Cancelled'`, `'Completed'`)

---

## 5. Security & Authorization Matrix

### 5.1. Authentication Controls
* **Guides (Staff)**: Start as `status = 'pending'` upon registration and are blocked from logging in until an admin approves them.
* **Trekkers (Users)**: Start as `status = 'approved'` and can log in immediately.
* **Blacklisted Accounts**: Blocked at login. If a user gets blacklisted while having an active session cookie, their session is invalidated globally by `user_loader` returning `None` immediately upon database lookup.

### 5.2. Role-Based Access Control (RBAC)
We implemented custom route decorators in `routes/utils.py` to enforce access levels:
* `@admin_required`: Gates administrative panels.
* `@staff_required`: Restricted to guides with role `'staff'` and status `'approved'`.
* `@user_required`: Restricted to trekkers with role `'user'`.

### 5.3. Parameter Tampering & IDOR Protections
* **Trek Ownership Check (`is_trek_owner`)**: Guides are blocked from accessing or updating treks led by other guides. If a guide manipulates the trek ID parameters in the address bar, the system aborts with an HTTP `403 Forbidden` error.
* **Booking Verification**: Users can only cancel bookings that belong to their own user identifier.
* **Input Limits Validation**: Added backend checks verifying `total_slots > 0` and `duration_days > 0` during trek creation/edit to block negative values.
* **Slot Capacity Locks**: Guides are prevented from setting `available_slots` to a value that (combined with active bookings) would exceed the trek's `total_slots` capacity.

### 5.4. SQL Injection Protection
* All search queries utilize SQLAlchemy's object-relational mapping APIs, which implement precompiled SQL statements under-the-hood. String parameter binding blocks SQL injection vectors.

---

## 6. Read-Only REST JSON API
To support external integrations, a read-only API is registered under `/api`:
* `GET /api/treks`: Public endpoint returning a serialized JSON list of all open trekking trips.
* `GET /api/bookings/<user_id>`: Password-protected/role-protected endpoint returning the target trekker's booking history.

---

## 7. Operational Testing & Verification
All components have undergone test passes validating redirects, bookings slot decrements, session cancellations, and registration approval states. The codebase compiles cleanly, and the database runs on SQLite dynamically.
