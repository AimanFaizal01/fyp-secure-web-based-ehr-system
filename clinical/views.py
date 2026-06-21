from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from patients.models import Patient
from .models import ClinicalNote, Diagnosis, Prescription, VitalSign
from .forms import ClinicalNoteForm, DiagnosisForm, PrescriptionForm, VitalSignForm
from accounts.decorators import doctor_required, nurse_required, clinical_staff_required
from accounts.utils import log_action


@login_required
@clinical_staff_required
def patient_records(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    clinical_notes = patient.clinical_notes.all()[:10]
    diagnoses = patient.diagnoses.all()[:10]
    prescriptions = patient.prescriptions.all()[:10]
    vital_signs = patient.vital_signs.all()[:10]
    
    log_action(request, 'View Clinical Records', resource='Patient', resource_id=patient.id,
               details=f'Accessed full clinical history for: {patient.first_name} {patient.last_name}')
    return render(request, 'clinical/patient_records.html', {
        'patient': patient,
        'clinical_notes': clinical_notes,
        'diagnoses': diagnoses,
        'prescriptions': prescriptions,
        'vital_signs': vital_signs,
    })


@login_required
@doctor_required
def add_clinical_note(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        form = ClinicalNoteForm(request.POST)
        if form.is_valid() or 'save_draft' in request.POST:
            note = form.save(commit=False)
            note.patient = patient
            note.doctor = request.user
            if 'save_draft' in request.POST:
                note.status = 'draft'
            note.save()
            
            status_text = 'Draft saved' if note.status == 'draft' else 'Clinical note added'
            log_action(request, 'Add Clinical Note', resource='Patient', resource_id=patient.id,
                       details=f'{status_text} for {patient.first_name} {patient.last_name}')
            messages.success(request, f'{status_text} successfully.')
            return redirect('clinical:patient_records', patient_id=patient.id)
    else:
        form = ClinicalNoteForm()
    return render(request, 'clinical/add_form.html', {
        'form': form,
        'patient': patient,
        'title': 'Add Clinical Note'
    })


@login_required
@doctor_required
def add_diagnosis(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        form = DiagnosisForm(request.POST)
        if form.is_valid():
            diagnosis = form.save(commit=False)
            diagnosis.patient = patient
            diagnosis.doctor = request.user
            diagnosis.save()
            log_action(request, 'Add Diagnosis', resource='Patient', resource_id=patient.id,
                       details=f'Diagnosis recorded for {patient.first_name} {patient.last_name}: {diagnosis.diagnosis}')
            messages.success(request, 'Diagnosis added successfully.')
            return redirect('clinical:patient_records', patient_id=patient.id)
    else:
        form = DiagnosisForm()
    return render(request, 'clinical/add_form.html', {
        'form': form,
        'patient': patient,
        'title': 'Add Diagnosis'
    })


@login_required
@doctor_required
def add_prescription(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.patient = patient
            prescription.doctor = request.user
            prescription.save()
            log_action(request, 'Add Prescription', resource='Patient', resource_id=patient.id,
                       details=f'Prescription issued for {patient.first_name} {patient.last_name}: {prescription.medication}')
            messages.success(request, 'Prescription added successfully.')
            return redirect('clinical:patient_records', patient_id=patient.id)
    else:
        form = PrescriptionForm()
    return render(request, 'clinical/add_form.html', {
        'form': form,
        'patient': patient,
        'title': 'Add Prescription'
    })


@login_required
@clinical_staff_required
def add_vital_signs(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == 'POST':
        form = VitalSignForm(request.POST)
        if form.is_valid():
            vital = form.save(commit=False)
            vital.patient = patient
            vital.recorded_by = request.user
            vital.save()
            log_action(request, 'Record Vital Signs', resource='Patient', resource_id=patient.id,
                       details=f'Vitals recorded for {patient.first_name} {patient.last_name}: BP {vital.blood_pressure}')
            messages.success(request, 'Vital signs recorded successfully.')
            return redirect('clinical:patient_records', patient_id=patient.id)
    else:
        form = VitalSignForm()
    return render(request, 'clinical/add_form.html', {
        'form': form,
        'patient': patient,
        'title': 'Record Vital Signs'
    })


@login_required
@clinical_staff_required
def patient_list_clinical(request):
    patients = Patient.objects.filter(is_active=True)
    log_action(request, 'View Clinical Patient List')
    return render(request, 'clinical/patient_list.html', {'patients': patients})
