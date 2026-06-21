# Implementation & Testing Guide

> **[ Project Home ](../README.md)** &nbsp;&nbsp; | &nbsp;&nbsp; **[ Implementation Guide ](IMPLEMENTATION_LOG.md)** &nbsp;&nbsp; | &nbsp;&nbsp; **[ Pentest Guide ](PENTEST_GUIDE.md)** &nbsp;&nbsp; | &nbsp;&nbsp; **[ ngrok Tunneling ](NGROK_SETUP.md)**

---

This document maps the project scope to the actual implemented features and explains how to test each one manually.

## 1. System Overview
**Scope:** Web-based EHR prototype, simulated hospital environment, functional modules, security focus.
**Implementation:** Built a full Django web app that handles hospital operations (patients, appointments, clinical records) with strict access controls.
**Test:** Run the server and go to `http://127.0.0.1:8000`. The login screen and dashboard reflect the hospital setup.

## 2. Technology Stack
**Scope:** Backend (Django), Frontend (HTML, CSS, Bootstrap), Database (PostgreSQL), Environment (localhost).
**Implementation:** Uses Django for the backend and plain HTML/CSS with Bootstrap icons for the frontend. 
**Test:** 
1. The system is coupled to an industrial-strength **PostgreSQL 15+** relational cluster locally and is production-scale ready.
2. **Audit Verification (Engine):** Run `psql -d hospital_ehr -c "SELECT version();"` in your terminal. Observe it returns the explicit PostgreSQL system header confirming the operational engine.
3. **Audit Verification (Crypto):** Run `psql -d hospital_ehr -c "\dx"` in your terminal. Observe that `pgcrypto` is formally listed as an active operational extension, certifying server-side readiness.

## 3. User Roles
**Scope:** Administrator, Doctor, Nurse, Receptionist with RBAC enforcement.
**Implementation:** Four hardcoded roles. Views and templates are restricted based on the logged-in user's role.
**Test:** 
1. Log in as `admin_hospital`.
2. Go to Staff Management and create a Doctor and a Receptionist account.
3. Log in as the Receptionist. Notice that you can't see or access Clinical Records or Administration menus. 
4. Log in as the Doctor. Notice you can't access Staff Management.

## 4. Core Functional Modules

### 4.1 User Management
**Scope:** Create/update/delete users, Assign roles (RBAC).
**Test:** Log in as Admin, go to Staff Management. Try editing a user's role or deleting an account.

### 4.2 Patient Management
**Scope:** Register patients, Update demographics, View patient info (Doctors: read-only access).
**Test:** 
1. **Authorized Flow:** Log in as Receptionist or Admin. Go to Patients, click Register Patient. Fill it out or hit "Save as Draft". You can also click "Edit Profile" on existing patients to update their details.
2. **Doctor Isolation Test:** Log in as a Doctor. Go to the Patient list. Verify that the "Register New Patient" button is completely hidden. Select any patient profile. Verify that the "Edit Profile" button is hidden. Attempt to manually visit a direct patient editing URL (e.g. `/patients/1/edit/`) and confirm you are strictly blocked.

### 4.3 Appointment Management
**Scope:** Schedule, Update/cancel, View list (Filtered lifecycle by role).
**Test:** 
1. **Receptionist Workflow:** Log in as a Receptionist, go to Appointments, and click "Update Status" on an existing entry. Verify that the dropdown options are strictly constrained to **Scheduled** or **Cancelled**.
2. **Doctor Workflow:** Log in as a Doctor. Verify the "New Appointment" creation button is completely hidden. Click "Update Status" on an appointment. Verify the dropdown options are strictly constrained to **Completed** or **Next Appointment Needed**.


### 4.4 Clinical Records
**Scope:** Store medical history, Add diagnosis/prescriptions, Role-based access.
**Test:** 
1. As a Doctor, open a patient's profile and go to Clinical Records.
2. Add a diagnosis and prescription.
3. Log in as a Nurse and go to the same page. The Nurse can only click "Record Vitals", not add diagnoses.
4. **Least Privilege Test:** Log in as `admin_hospital`. Verify that the "Clinical Records" tab is completely hidden from view across the whole portal. Try manually visiting `/clinical/patients/` and verify you are redirected back with a hard "Access Denied" error.

### 4.5 Dashboard
**Scope:** Dashboard interface, Role-based dashboards.
**Test:** Check the homepage after logging in. Admins see security alerts and user stats. Doctors only see clinical stats (total patients, appointments).

## 5. Security Requirements

### 5.1 Access Control (RBAC & RAAC)
**Scope:** RBAC, RAAC (Abnormal behavior detection, Step-up auth).
**Implementation:** Besides basic RBAC, there's a custom Risk-Aware Access Control (RAAC) middleware that enforces a **Continuous Adaptive Risk Loop**:
* **Risk Accumulation:** Every detected suspicious event increases user security risk by `+25%`.
* **Step-Up Verification:** If risk exceeds `40%`, Step-Up MFA is triggered automatically.
* **Risk Hysteresis:** Passing the MFA challenge reduces the score by `25%` but does NOT fully wipe it (leaving a trace memory of past abnormal actions).
* **Emergency Lockout:** If the cumulative risk stacks up to `100%`, the middleware automatically locks the account, blocking further MFA verification attempts and forcing Administrative intervention.
**Test RAAC (5 Behavioral Threat Models):** 
1. **Data Harvesting (Multi-profile access):** Log in, go to the Patient Registry, and middle-click **5 different patient profiles** to open them in rapid succession. The system flags `"Data Harvesting"` and redirects to Step-Up MFA verification.
2. **Data Scraping (Deep reading):** Go into a single patient's profile and refresh details or clinical records **more than 20 times** in rapid succession. The system flags `"Data Scraping"` and locks the session behind MFA.
3. **Privilege/Admin Probing (Reconnaissance):** Log in as an Admin, go to User Management or Audit Logs, and refresh or click through these logs **more than 15 times** in rapid succession. The system flags `"Privilege Probing"` and triggers Step-Up MFA.
4. **Record Tampering (Bulk modifications):** Rapidly add clinical notes, vitals, or edit records **more than 10 times** in rapid succession. The system flags `"Record Tampering"` and forces MFA verification.
5. **Navigation Flood (Inhuman crawling velocity):** Rapidly navigate between random sidebar tabs **more than 40 times** in under 2 minutes. The system flags `"Navigation Flood"` and prompts Step-Up MFA.
6. **Cumulative Adaptive Lockout (Risk Trap):** Trigger alarms (+25%), pass MFA (reduces by 25% keeping memory), and repeat until cumulative risk hits 100%. The system automatically hard-locks the user and blocks all further MFA verification attempts.

#### 5.2 & 5.3 Auth & Password Security
**Scope:** Username/password, MFA (TOTP), Django PBKDF2 hashing, Password Reset, Account Lockout & Admin Unlocking.
**Implementation:** 
* Uses Django's default PBKDF2 hashing. 
* **Mandatory TOTP MFA:** Multi-factor authentication is strictly enforced for all authenticated sessions. Middleware intercepts first-time logins and forcefully routes users to a Security Setup Wizard. **Exemptions:** Administrators can explicitly flag individual high-clearance or non-sensitive user profiles as "Exempt" via the dashboard to bypass verification gating when necessary. Deactivation remains blocked for self-service users.
* Integrated secure **Password Recovery** using **Resend SMTP**, sending a secure **6-digit verification code** to the user's mailbox with dynamic **MFA gating** (forcing authenticator code verification if MFA is active).
* **Account Lockout:** If a user inputs 5 consecutive incorrect passwords or 5 consecutive incorrect MFA codes, the account is automatically locked (`is_locked = True`).
* **Admin Unlocking:** Administrators can view locked users in the Staff Management console and click the dedicated green **Unlock Account** (`bi-unlock`) action button, which instantly resets `is_locked` to False, flushes security risk scores to `0%`, and clears failed attempt counters to `0`.
**Test:**
1. Check the database to see that passwords are hashed.
2. Log in with a new account. The system will instantly divert you to the "Security Activation Required" page, blocking dashboard access until configured.
3. Follow activation steps. Observe you can now enter the workspace, and notice the 'Disable MFA' action is strictly hidden/blocked for your role.
4. **Account Lockout Test:** Attempt to log in with an incorrect password 5 times in a row. The account will lock.
5. **Admin Unlock Test:** Log in as `admin_hospital`, go to Staff Management (`/accounts/users/`), locate the locked user, click the green **Unlock** button, confirm the popup, and verify the user can log in again.
* **Password Recovery Test:** On the login screen, click **Forgot Password?**. Submit your email, check your real inbox for the Resend verification code, enter the code in the interface, and verify that the system forces an MFA code check if MFA is enabled (or bypasses it securely if disabled).

#### 5.4 Forced First-Login Password Change
**Scope:** Compel newly onboarded staff to upgrade their temporary admin-assigned credentials before they can access any workspace features or initiate visual MFA wizards. Ensures the Administrator maintains a complete blind spot over permanent user passwords.
**Implementation:**
* **AES-256 GCM Transient Buffer:** When an admin creates an account, the typed temporary password is set on the user AND written to a dedicated **`temp_password` EncryptedCharField**, scrambing it instantly at rest with **AES-256 GCM** cipher suites.
* **Precedence Interceptor Gate:** The custom authentication middleware monitors the `needs_password_change` boolean. If `True`, it seizes the request sequence and forces a redirect to a standalone, brand-isolated **Activation Gateway**, completely bypassing visual MFA configurations until resolved.
* **Cryptographic Erasure:** Upon a successful password update, the database pipeline immediately sets `needs_password_change = False` and **permanently nulls** the `temp_password` AES-256 field, eliminating all traces of the temporary credential from the server entirely.
**Test:**
1. Log in as Admin and create a new user `temp_doctor`. Choose any initial password.
2. Log out and attempt to sign in as `temp_doctor` using that password.
3. The system must instantly hijack your session, preventing you from viewing the dashboard or the MFA setup wizard, landing you on the clean `Reset Password` brand card.
4. Type a new secure password. Observe you are immediately released to finalize visual Multi-Factor Authentication setup.
5. **Zero-Leak Audit:** Inspect the SQL database records for `temp_doctor` immediately after creation (observe scrambled ciphertext) and after their first login (observe the field has been securely purged to `NULL`).


## 6. Data Security & Encryption
**Scope:** AES-256 encryption, Sensitive data encryption, HTTPS, Blowfish.
**Implementation:** Highly sensitive fields (like patient phone numbers and clinical notes) are encrypted at rest using an authenticated **AES-256 GCM** algorithm architecture coupled to a high-availability PostgreSQL backend with standard `pgcrypto` activated at the database engine level.
**Test:** 
1. Register a patient with a unique phone number like `555-999-1234`.
2. Connect to the SQL Database via terminal or viewer (`psql -d hospital_ehr`). 
3. Run a `SELECT * FROM patients_patient;`. You will observe that sensitive data columns reside strictly as encoded ciphertext blocks, preventing raw database data exfiltration.

## 7. Web Security (OWASP)
**Scope:** SQL Injection, XSS, CSRF protection, Input validation.
**Implementation:** Relying on Django's built-in protections.
**Test:**
1. SQLi/XSS: Try registering a patient with the first name `<script>alert(1)</script>`. It will just display as text, no script execution.
2. CSRF: Inspect any form (like the login form). You'll see a hidden `csrfmiddlewaretoken` input.

## 8. Session & Access Control
**Scope:** Session system, Session timeout, Role-based page restriction.
**Implementation:** Sessions are set to expire when the browser closes.
**Test:** Log in, then completely close your web browser. Reopen it and go back to the app. You'll be logged out and asked to sign in again.

## 9. Logging & Monitoring
**Scope:** Log login attempts, Log patient record access, Log suspicious activity, Admin log viewer.
**Implementation:** Custom audit log model tracks read/write actions across the app.
**Test:** 
1. Log in as a Doctor and view some patient records.
2. Log in as Admin and go to Audit Logs. 
3. You'll see a list of who did what, when, and from what IP. Suspicious RAAC alerts will also show up here.
