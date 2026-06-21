# A Secure Web-Based EHR System

---

This is a web-based Electronic Health Record (EHR) prototype built with Django. It simulates a hospital environment with functional modules for patients, appointments, and staff management, with a heavy focus on security and RBAC.

## Setup Instructions

Make sure to have Python installed (3.8+).

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # on Windows use: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup PostgreSQL Database:
   The system utilizes an enterprise PostgreSQL backend. Ensure you have PostgreSQL installed (`brew install postgresql@15` on Mac) and running, then create the database container:
   ```bash
   createdb hospital_ehr
   ```

4. Run the setup migrations:
   ```bash
   python3 manage.py migrate
   ```

5. Run the development server:
   ```bash
   python3 manage.py runserver
   ```

6. Open your browser and go to `http://127.0.0.1:8000`

## Creating an Administrator Account
Because the database is blank on fresh deployments, you can generate the master administrator account directly from your terminal. 

The system has been programmed to automatically map the "Administrator" clearance role to any terminal-created root users. Simply run:

```bash
python3 manage.py createsuperuser
```

*(Alternatively, to create a hardcoded admin account instantly via scripting, run:)*
```bash
python3 manage.py shell -c "from accounts.models import User; u, created = User.objects.get_or_create(username='admin_hospital', defaults={'email': 'admin@hospital.com'}); u.set_password('Hospital123!'); u.is_superuser=True; u.is_staff=True; u.role='admin'; u.save(); print('Admin account set up successfully!')"
```

Once configured, log in at `http://127.0.0.1:8000` using:
- **Username:** `admin_hospital`
- **Password:** `Hospital123!`

From the **Staff Management** tab inside the dashboard, you can create other accounts (Doctors, Nurses, Receptionists) to test their respective permissions.

## Seeding Demo Data
Instantly populate the system with realistic Malaysian hospital patients, clinical records, and pre-configured staff accounts, run:
```bash
python3 manage.py seed_malaysian_data
```
This will generate:
* **Doctors:** `dr_ahmad`, `dr_siti`, `dr_raj`
* **Nurse:** `nurse_maya`
* **Receptionist:** `reception_anna`
* **Administrator:** `admin_wee`
*(All pre-seeded accounts use the password `password123`)*

