from django.db import models
from django.conf import settings
from patients.models import Patient
from config.encryption import EncryptedCharField, EncryptedTextField

class Appointment(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        CHECKED_IN = 'checked_in', 'Checked In'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'
        FOLLOW_UP = 'follow_up', 'Next Appointment Needed'

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='doctor_appointments',
        limit_choices_to={'role': 'doctor'}
    )
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    reason = EncryptedTextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    notes = EncryptedTextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='appointments_created'
    )

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.patient} - {self.date} {self.time}"
