# FixIt - Apartment Maintenance System

Django-based web application for managing apartment maintenance requests. Tenants submit issues, managers assign technicians, technicians complete work.

## Quick Start (5 min)

```bash
git clone < https://github.com/gimshaninethmini/apartment_maintainance_system >
cd apartment_maintainance_system
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python create_users.py          # Option A: Create all test accounts
# OR
python manage.py createsuperuser  # Option B: Create admin only
python manage.py runserver
```

Visit `http://localhost:8000/login/`

---

## Create Accounts

**Option 1: Auto-create all test accounts**
```bash
python create_users.py
```
Creates: `admin` (superuser), `tenant1`, `tech1`, `manager1`

**Option 2: Create admin only**
```bash
python manage.py createsuperuser
```

**Admin Panel:** `http://localhost:8000/admin/`

---

## Features

- Submit maintenance requests with images
- Real-time status tracking
- Assign technicians to requests
- Track request history & logs
- Export data as CSV
- Role-based access control

---

## User Roles

**Tenant:** Submit requests • Track status • Edit/cancel pending requests

**Manager:** View all requests • Assign technicians • Update status • Export CSV

**Technician:** View assigned tasks • Update progress • Add notes

---

## Database Models

| Model | Purpose |
|-------|---------|
| `MaintenanceRequest` | Submitted issues (tenant, title, description, image, status, priority) |
| `UserProfile` | User role & info (role, phone, apartment_number) |
| `Assignment` | Technician assignment (technician, request, notes) |
| `UpdateLog` | Status history (status, notes, updated_by, created_at) |

---

## Request Status Flow

```
Submitted → Reviewed → Assigned → In Progress → Completed (or Cancelled)
```

---

## Main Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/login/` | User login |
| `/register/` | Create account |
| `/dashboard/` | Main dashboard |
| `/submit/` | Submit request |
| `/request/<id>/` | View request |
| `/manager/request/<id>/` | Manager view & assign |
| `/manager/export/` | Download CSV |
| `/update/<id>/` | Technician update |
| `/profile/` | Edit profile |

---

## Common Tasks

**Reset Database**
```bash
rm db.sqlite3
python manage.py migrate
python create_users.py
```

**Access Admin**
```
URL: http://localhost:8000/admin/
Login: superuser account
```

**Create Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Run Tests**
```bash
python manage.py test
```

---

## Troubleshooting

**Port 8000 in use?**
```bash
python manage.py runserver 8001
```

**Database errors?**
```bash
python manage.py migrate
```

**Can't login as manager?**
- Go to `/admin/` → Set `manager_approved = True`

**Module not found?**
```bash
pip install -r requirements.txt
```

---

## Project Structure

```
├── apartmentsystem/       # Django config (settings.py, urls.py)
├── maintenance/          # Main app (models.py, views.py)
├── templates/            # HTML files
├── static/               # CSS, JS
├── media/                # User uploads
├── manage.py             # Django CLI
├── create_users.py       # Create test users
├── requirements.txt      # Dependencies: Django==6.0.3, pillow
└── db.sqlite3           # SQLite database
```

---

## Configuration

**Database:** SQLite (development)

**Key Settings (apartmentsystem/settings.py):**
- `DEBUG = True`
- `ALLOWED_HOSTS = []`
- `SECRET_KEY` (change for production)

**For Production:**
- Set `DEBUG = False`
- Change `SECRET_KEY`
- Use PostgreSQL
- Enable HTTPS
- Use Gunicorn/uWSGI

---
