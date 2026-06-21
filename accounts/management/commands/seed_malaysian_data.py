from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from patients.models import Patient
from appointments.models import Appointment
from clinical.models import ClinicalNote, Diagnosis, Prescription, VitalSign
from datetime import date, time, timedelta
from random import randint, choice

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds Malaysian hospital data including patients, staff, appointments, and clinical records'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Malaysian hospital data...')
        
        # Clear existing data
        VitalSign.objects.all().delete()
        Prescription.objects.all().delete()
        Diagnosis.objects.all().delete()
        ClinicalNote.objects.all().delete()
        Appointment.objects.all().delete()
        Patient.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        # Create Staff Users
        staff_data = [
            {'username': 'dr_ahmad', 'first_name': 'Ahmad', 'last_name': 'Bin Ibrahim', 'role': 'doctor', 'phone': '+60-12-345-6789'},
            {'username': 'dr_siti', 'first_name': 'Siti', 'last_name': 'Nur Binti Rahman', 'role': 'doctor', 'phone': '+60-12-345-6790'},
            {'username': 'dr_raj', 'first_name': 'Raj', 'last_name': 'A/L Kumar', 'role': 'doctor', 'phone': '+60-12-345-6791'},
            {'username': 'nurse_maya', 'first_name': 'Maya', 'last_name': 'Amani Binti', 'role': 'nurse', 'phone': '+60-12-345-6792'},
            {'username': 'reception_anna', 'first_name': 'Anna', 'last_name': 'Lee Mei Ling', 'role': 'receptionist', 'phone': '+60-12-345-6793'},
            {'username': 'admin_wee', 'first_name': 'Wee', 'last_name': 'Jia Min', 'role': 'admin', 'phone': '+60-12-345-6794'},
        ]
        
        doctors = []
        for staff in staff_data:
            user = User.objects.create_user(
                username=staff['username'],
                email=f"{staff['username']}@hospital.com",
                password='password123',
                first_name=staff['first_name'],
                last_name=staff['last_name'],
                phone=staff['phone'],
                role=staff['role']
            )
            if staff['role'] == 'doctor':
                doctors.append(user)
            self.stdout.write(f'Created staff: {user}')
        
        # Create Malaysian Patients
        malaysian_patients = [
            {'first_name': 'Muhammad', 'last_name': 'Bin Zulkifli', 'dob': date(1985, 3, 15), 'gender': 'M', 
             'phone': '+60-11-1234-5678', 'email': 'muhammad.z@email.com',
             'address': 'No. 15, Jalan Taman Sri Bahagia, 51200 Kuala Lumpur',
             'emergency_contact_name': 'Zulkifli Bin Ahmad', 'emergency_contact_phone': '+60-11-9876-5432'},
            {'first_name': 'Lim', 'last_name': 'Mei Ling', 'dob': date(1990, 7, 22), 'gender': 'F',
             'phone': '+60-10-2345-6789', 'email': 'meiling.lim@email.com',
             'address': '23, Lebuh Sungai Pinang, 10100 George Town, Penang',
             'emergency_contact_name': 'Lim Choon Swee', 'emergency_contact_phone': '+60-10-2345-6790'},
            {'first_name': 'Ahmad', 'last_name': 'Fadzir Bin', 'dob': date(1978, 11, 8), 'gender': 'M',
             'phone': '+60-13-4567-8901', 'email': 'ahmad.fadzir@email.com',
             'address': 'No. 45, Taman Melaka Raya, 75000 Melaka',
             'emergency_contact_name': 'Fadzir Bin Abdullah', 'emergency_contact_phone': '+60-13-4567-8902'},
            {'first_name': 'Siti', 'last_name': 'Nurhaliza Binti Kamal', 'dob': date(1995, 5, 30), 'gender': 'F',
             'phone': '+60-14-6789-0123', 'email': 'siti.nurhaliza@email.com',
             'address': 'No. 78, Jalan Ismail Petra, 16100 Kota Bharu, Kelantan',
             'emergency_contact_name': 'Kamal Bin Mahmud', 'emergency_contact_phone': '+60-14-6789-0124'},
            {'first_name': 'Kumar', 'last_name': 'A/L Muthu', 'dob': date(1982, 9, 12), 'gender': 'M',
             'phone': '+60-16-7890-1234', 'email': 'kumar.muthu@email.com',
             'address': 'No. 12, Jalan Besi, 80100 Johor Bahru, Johor',
             'emergency_contact_name': 'Muthu Veerasamy', 'emergency_contact_phone': '+60-16-7890-1235'},
            {'first_name': 'Chloe', 'last_name': 'Tan Wei Ling', 'dob': date(2000, 2, 14), 'gender': 'F',
             'phone': '+60-17-8901-2345', 'email': 'chloe.tan@email.com',
             'address': 'No. 34, Lorong Hill, 93300 Kuching, Sarawak',
             'emergency_contact_name': 'Tan Hock Seng', 'emergency_contact_phone': '+60-17-8901-2346'},
            {'first_name': 'Mohd', 'last_name': 'Razif Bin Roslan', 'dob': date(1988, 12, 25), 'gender': 'M',
             'phone': '+60-18-9012-3456', 'email': 'mohd.razif@email.com',
             'address': 'No. 56, Kg. Melayu, 15200 Kota Bharu, Kelantan',
             'emergency_contact_name': 'Roslan Bin Idris', 'emergency_contact_phone': '+60-18-9012-3457'},
            {'first_name': 'Ng', 'last_name': 'Ming Fatt', 'dob': date(1975, 6, 18), 'gender': 'M',
             'phone': '+60-19-0123-4567', 'email': 'ng.mingfatt@email.com',
             'address': 'No. 89, Taman Sentosa, 41200 Klang, Selangor',
             'emergency_contact_name': 'Ng Chin Chuan', 'emergency_contact_phone': '+60-19-0123-4568'},
            {'first_name': 'Fatimah', 'last_name': 'Binti Abdullah', 'dob': date(1992, 4, 7), 'gender': 'F',
             'phone': '+60-19-2345-6789', 'email': 'fatimah.abd@email.com',
             'address': 'No. 21, Jalan Pokok Mangga, 21100 Kuantan, Pahang',
             'emergency_contact_name': ' Abdullah Bin Hassan', 'emergency_contact_phone': '+60-19-2345-6790'},
            {'first_name': 'Prashanth', 'last_name': 'A/L Subramaniam', 'dob': date(1987, 8, 21), 'gender': 'M',
             'phone': '+60-19-3456-7890', 'email': 'prashanth.s@email.com',
             'address': 'No. 67, Jalan Selangor, 40000 Shah Alam, Selangor',
             'emergency_contact_name': 'Subramaniam A/L Gopal', 'emergency_contact_phone': '+60-19-3456-7891'},
        ]
        
        patients = []
        for p_data in malaysian_patients:
            patient = Patient.objects.create(
                first_name=p_data['first_name'],
                last_name=p_data['last_name'],
                date_of_birth=p_data['dob'],
                gender=p_data['gender'],
                phone=p_data['phone'],
                email=p_data['email'],
                address=p_data['address'],
                emergency_contact_name=p_data['emergency_contact_name'],
                emergency_contact_phone=p_data['emergency_contact_phone'],
                created_by=doctors[0]
            )
            patients.append(patient)
            self.stdout.write(f'Created patient: {patient}')
        
        # Create Appointments
        appointment_reasons = [
            'General Check-up', 'Follow-up consultation', 'Fever and flu symptoms',
            'Joint pain examination', 'Skin rash evaluation', 'Blood pressure monitoring',
            'Diabetes management review', 'Chest pain assessment', 'Headache consultation',
            'Annual health screening'
        ]
        
        appointment_statuses = ['scheduled', 'checked_in', 'in_progress', 'completed', 'cancelled']
        
        for i, patient in enumerate(patients):
            # Create 2-4 appointments per patient
            for j in range(randint(2, 4)):
                appt_date = date.today() + timedelta(days=randint(-30, 30))
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=choice(doctors),
                    date=appt_date,
                    time=time(randint(8, 16), randint(0, 59)),
                    reason=choice(appointment_reasons),
                    status=choice(appointment_statuses),
                    created_by=doctors[0]
                )
                self.stdout.write(f'Created appointment: {appointment}')
        
        # Create Clinical Records for each patient
        diagnoses_list = [
            ('Hypertension', 'Elevated blood pressure readings consistently above 140/90 mmHg'),
            ('Type 2 Diabetes Mellitus', 'Elevated blood glucose levels requiring medication'),
            ('Acute Bronchitis', 'Inflammation of the bronchial tubes causing cough'),
            ('Gastroesophageal Reflux Disease', 'Chronic acid reflux condition'),
            ('Migraine', 'Recurring headaches with visual disturbances'),
            ('Allergic Rhinitis', 'Seasonal allergies affecting nasal passages'),
            ('Asthma', 'Chronic respiratory condition requiring inhaler'),
            ('Hyperlipidemia', 'Elevated cholesterol levels'),
            ('Osteoarthritis', 'Joint degeneration in knee and hip'),
            ('Anxiety Disorder', 'Generalized anxiety requiring management'),
        ]
        
        medications = [
            ('Paracetamol 500mg', '500mg', 'Three times daily', '7 days', 'Take after meals'),
            ('Amoxicillin 250mg', '250mg', 'Twice daily', '10 days', 'Complete full course'),
            ('Metformin 500mg', '500mg', 'Twice daily', '30 days', 'Take with food'),
            ('Lisinopril 10mg', '10mg', 'Once daily', '30 days', 'Monitor blood pressure'),
            ('Atorvastatin 20mg', '20mg', 'Once daily', '30 days', 'Take at night'),
            ('Salbutamol Inhaler', '100mcg', 'As needed', '30 days', 'Use when wheezing'),
            ('Omeprazole 20mg', '20mg', 'Once daily', '14 days', 'Take before breakfast'),
            ('Ibuprofen 400mg', '400mg', 'Three times daily', '5 days', 'Take after meals'),
        ]
        
        for patient in patients:
            # Create diagnosis
            diagnosis = choice(diagnoses_list)
            Diagnosis.objects.create(
                patient=patient,
                doctor=choice(doctors),
                diagnosis=diagnosis[0],
                description=diagnosis[1]
            )
            
            # Create prescription
            med = choice(medications)
            Prescription.objects.create(
                patient=patient,
                doctor=choice(doctors),
                medication=med[0],
                dosage=med[1],
                frequency=med[2],
                duration=med[3],
                instructions=med[4]
            )
            
            # Create vital signs
            VitalSign.objects.create(
                patient=patient,
                recorded_by=choice(doctors),
                blood_pressure_systolic=randint(110, 160),
                blood_pressure_diastolic=randint(70, 100),
                pulse_rate=randint(60, 100),
                temperature=round(randint(360, 380) / 10.0, 1),
                respiratory_rate=randint(12, 20),
                notes='Routine vital signs measurement'
            )
            
            # Create clinical note
            ClinicalNote.objects.create(
                patient=patient,
                doctor=choice(doctors),
                note=f'Patient {patient.full_name} presented with symptoms. Assessment completed. Treatment plan discussed with patient. Follow-up scheduled.'
            )
            
            self.stdout.write(f'Created clinical records for: {patient}')
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded Malaysian hospital data!'))
        self.stdout.write('\nStaff Login Credentials:')
        for staff in staff_data:
            self.stdout.write(f'  Username: {staff["username"]}, Password: password123')
