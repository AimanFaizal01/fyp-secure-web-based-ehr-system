from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Patient
from .forms import PatientForm
from accounts.decorators import receptionist_required, admin_required
from accounts.utils import log_action


@login_required
def patient_list(request):
    query = request.GET.get('q', '')
    patients = Patient.objects.all()
    
    if query:
        patients = patients.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )
    
    log_action(request, 'View Patient List')
    return render(request, 'patients/patient_list.html', {
        'patients': patients,
        'query': query
    })


@login_required
@receptionist_required
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            if 'save_draft' in request.POST:
                patient.status = Patient.Status.DRAFT
            patient.created_by = request.user
            patient.save()
            
            status_text = 'Draft saved' if patient.status == Patient.Status.DRAFT else 'Patient registered'
            log_action(request, 'Create Patient Record', resource='Patient', resource_id=patient.id,
                       details=f'{status_text}: {patient.first_name} {patient.last_name}')
            messages.success(request, f'{status_text} successfully.')
            return redirect('patients:patient_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientForm()
    return render(request, 'patients/patient_form.html', {
        'form': form,
        'title': 'Register Patient'
    })


@login_required
@receptionist_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save(commit=False)
            if 'save_draft' in request.POST:
                patient.status = Patient.Status.DRAFT
            patient.save()
            
            status_text = 'Draft saved' if patient.status == Patient.Status.DRAFT else 'Patient record updated'
            log_action(request, 'Edit Patient Record', resource='Patient', resource_id=patient.id,
                       details=f'{status_text}: {patient.first_name} {patient.last_name}')
            messages.success(request, f'{status_text} successfully.')
            return redirect('patients:patient_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patients/patient_form.html', {
        'form': form,
        'title': 'Edit Patient'
    })


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    log_action(request, 'View Patient Detail', resource='Patient', resource_id=patient.id,
               details=f'Accessed profile: {patient.first_name} {patient.last_name}')
    return render(request, 'patients/patient_detail.html', {'patient': patient})


@login_required
@receptionist_required
def patient_toggle_active(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    patient.is_active = not patient.is_active
    patient.save()
    status = 'activated' if patient.is_active else 'deactivated'
    log_action(request, 'Toggle Patient Status', resource='Patient', resource_id=patient.id,
               details=f'Patient {patient.first_name} {patient.last_name} {status}')
    messages.success(request, f'Patient {patient.full_name} has been {status}.')
    return redirect('patients:patient_list')


@login_required
@admin_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    patient_name = f"{patient.first_name} {patient.last_name}"
    
    log_action(request, 'Delete Patient Record', resource='Patient', resource_id=pk,
               details=f'PERMANENT DELETION of patient record: {patient_name}')
    
    patient.delete()
    messages.warning(request, f'Patient record for {patient_name} has been permanently deleted.')
    return redirect('patients:patient_list')
