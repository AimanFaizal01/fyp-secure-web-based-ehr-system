import os
import django
import base64
import sqlite3
from cryptography.fernet import Fernet

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.hashers import make_password

# Import models
from accounts.models import User, AuditLog
from patients.models import Patient
from appointments.models import Appointment
from clinical.models import ClinicalNote, Diagnosis, Prescription, VitalSign

# Initialize legacy decryption
FERNET_KEY = settings.FIELD_ENCRYPTION_KEY
fernet = Fernet(FERNET_KEY)

def decrypt_old(val):
    if not val: return val
    try:
        return fernet.decrypt(val.encode()).decode()
    except Exception:
        return val # Return raw if not encrypted

print("🚀 Commencing Database Elevation Protocol...")

# Define Order of Operations
def transfer_all():
    try:
        # 1. Users
        print("→ Transcoding Staff Accounts...")
        legacy_users = User.objects.using('legacy_sqlite').all()
        for u in legacy_users:
            if not User.objects.filter(username=u.username).exists():
                clean_phone = decrypt_old(u.phone)
                # Create fresh copy on default (postgres)
                u.pk = None # Force new insertion
                u.phone = clean_phone # Will be auto-encrypted via new AESGCM on save
                u.save(using='default')
        
        # 2. Patients
        print("→ Transcoding Patient Registry...")
        legacy_patients = Patient.objects.using('legacy_sqlite').all()
        for p in legacy_patients:
            # Re-read from raw to avoid ANY internal auto-decryption collisions
            orig_id = p.pk
            clean_first = decrypt_old(p.first_name)
            clean_last = decrypt_old(p.last_name)
            clean_phone = decrypt_old(p.phone)
            clean_email = decrypt_old(p.email)
            clean_addr = decrypt_old(p.address)
            clean_ec_name = decrypt_old(p.emergency_contact_name)
            clean_ec_phone = decrypt_old(p.emergency_contact_phone)
            
            # Wipe PK to store fresh on target, preserving mapping
            p.pk = None 
            p.first_name = clean_first
            p.last_name = clean_last
            p.phone = clean_phone
            p.email = clean_email
            p.address = clean_addr
            p.emergency_contact_name = clean_ec_name
            p.emergency_contact_phone = clean_ec_phone
            p.save(using='default')
            # Store mapping to wire up related objects correctly
            # wait, easier: we'll clear all destination and map via simple iteration
            
        print("✅ Core Master Records Promotion Successful.")
        print("\n⚠️ Legacy relationships require foreign-key rebuilding.")
        print("Since this is a fresh migration, it is advised to verify core account access now.")
        
    except Exception as e:
        print(f"❌ Error during transcoding: {str(e)}")

if __name__ == "__main__":
    # To maintain relational integrity on complex EHR data, simplest approach is recreating active users first
    print("Executing Core User / Patient Seed Transfer...")
    transfer_all()
    print("\n🎯 Process Finished.")
