# TrekVoyage - Trekking Management System V1

TrekVoyage is a modern, modular, and role-based web application built with Python and the Flask micro-framework. It is designed to coordinate outdoor trekking expeditions, staff (guides), and users (trekkers) with an elegant, responsive UI styled using Bootstrap 5 and custom CSS tokens.

---

## Key Features

* **Role-Based Access Control (RBAC)**: Distinct blueprints, portals, and decorators for Admins, Guides (Staff), and Trekkers (Users).
* **Interactive Admin Dashboard**: Quick statistics metrics, guide assignment tools, and a dynamic bookings-per-trek visualization bar chart powered by Chart.js.
* **Guide Portal**: Handles trek statuses, slots management, and lists registered participants for assigned treks.
* **Trekker Portal**: Catalog search and filters (by difficulty & location), real-time booking, active cancellations (with slot replenishment), and profile editing.
* **Secure REST API**: Read-only JSON endpoints for open treks catalog and user-restricted booking logs.
* **Hardened Security Gaps**: Closed SQL Injection vulnerabilities via ORM parameterized queries, blocked Insecure Direct Object References (IDOR), capped slots boundaries, and implemented session invalidation for blacklisted accounts.

---

## Tech Stack

* **Backend Framework**: Flask 3.x
* **Database**: SQLite (managed programmatically via Flask-SQLAlchemy)
* **Authentication**: Flask-Login (session-based)
* **Frontend styling**: Bootstrap 5, Custom CSS variables, Bootstrap Icons
* **Charts & Visuals**: Chart.js (CDN)

---

## Installation & Local Setup

### 1. Prerequisite
* Python 3.8+ installed on your system.

### 2. Set Up Virtual Environment & Install Dependencies
Clone the repository and open a terminal inside the `trekking_app` project directory:
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
Initialize the SQLite database schema and seed the default Administrator account:
```powershell
python seed.py
```

### 4. Run Flask Server
Launch the development server in debug mode:
```powershell
python -m flask run --debug
```
Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## Default Testing Credentials

For evaluation and testing, you can use the default seeded admin account or register new ones via the portal:

* **Administrator**:
  * **Email**: `admin@trekvoyage.com`
  * **Password**: `admin123` (or the custom password set during seeding)
* **Guide Registration**: Register on the website. To activate, log in as Admin and navigate to **Manage Staff** to click **Approve**.

---

## JSON REST API Endpoints

* **Get Open Treks**: `GET /api/treks` (Public)
  * Returns list of open trekking trips.
* **Get Booking History**: `GET /api/bookings/<user_id>` (Auth-Protected)
  * Returns user booking logs. Restricting access to booking owner or system admin.
