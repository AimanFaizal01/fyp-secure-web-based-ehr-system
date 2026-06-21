from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Appointment
from .forms import AppointmentForm, AppointmentStatusForm
from accounts.decorators import receptionist_required, clinical_staff_required
from accounts.utils import log_action


@login_required
def appointment_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    appointments = Appointment.objects.select_related('patient', 'doctor')
    
    if query:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query) |
            Q(doctor__first_name__icontains=query) |
            Q(doctor__last_name__icontains=query)
        )
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    log_action(request, 'View Appointment List')
    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments,
        'query': query,
        'status_filter': status_filter,
        'status_choices': Appointment.Status.choices
    })


@login_required
@receptionist_required
def appointment_create(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            if 'save_draft' in request.POST:
                appointment.status = Appointment.Status.DRAFT
            
            appointment.created_by = request.user
            appointment.save()
            
            status_text = 'Draft saved' if appointment.status == Appointment.Status.DRAFT else 'Appointment scheduled'
            log_action(request, 'Create Appointment', resource='Appointment', resource_id=appointment.id,
                       details=f'{status_text} for {appointment.date} with Dr. {appointment.doctor}')
            messages.success(request, f'{status_text} successfully.')
            return redirect('appointments:appointment_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AppointmentForm()
    return render(request, 'appointments/appointment_form.html', {
        'form': form,
        'title': 'Create Appointment'
    })


@login_required
@receptionist_required
def appointment_edit(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            appointment = form.save(commit=False)
            if 'save_draft' in request.POST:
                appointment.status = Appointment.Status.DRAFT
            appointment.save()
            
            status_text = 'Draft saved' if appointment.status == Appointment.Status.DRAFT else 'Appointment updated'
            log_action(request, 'Edit Appointment', resource='Appointment', resource_id=appointment.id,
                       details=f'{status_text} for #{appointment.id}')
            messages.success(request, f'{status_text} successfully.')
            return redirect('appointments:appointment_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AppointmentForm(instance=appointment)
    return render(request, 'appointments/appointment_form.html', {
        'form': form,
        'title': 'Edit Appointment'
    })


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    log_action(request, 'View Appointment Detail', resource='Appointment', resource_id=appointment.id)
    return render(request, 'appointments/appointment_detail.html', {'appointment': appointment})


@login_required
def appointment_update_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        old_status = appointment.get_status_display()
        form = AppointmentStatusForm(request.POST, instance=appointment, user=request.user)
        if form.is_valid():
            form.save()
            new_status = appointment.get_status_display()
            log_action(request, 'Update Appointment Status', resource='Appointment', resource_id=appointment.id,
                       details=f'Status changed from {old_status} to {new_status}')
            messages.success(request, 'Appointment status updated.')
            return redirect('appointments:appointment_list')
    else:
        form = AppointmentStatusForm(instance=appointment, user=request.user)
    return render(request, 'appointments/appointment_status_form.html', {
        'form': form,
        'appointment': appointment
    })


@login_required
@receptionist_required
def appointment_delete(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    patient_name = f"{appointment.patient.first_name} {appointment.patient.last_name}"
    
    log_action(request, 'Delete Appointment', resource='Appointment', resource_id=pk,
               details=f'Deleted appointment for {patient_name} scheduled on {appointment.date}')
    
    appointment.delete()
    messages.warning(request, 'Appointment has been permanently deleted.')
    return redirect('appointments:appointment_list')
