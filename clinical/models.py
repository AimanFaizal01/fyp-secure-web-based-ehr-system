from django.db import models
from django.conf import settings
from patients.models import Patient
from config.encryption import EncryptedCharField, EncryptedTextField


class ClinicalNote(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='clinical_notes'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clinical_notes'
    )
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        FINAL = 'final', 'Final'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.FINAL)
    note = EncryptedTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.patient} by {self.doctor} on {self.created_at.date()}"


class Diagnosis(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='diagnoses'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='diagnoses'
    )
    diagnosis = EncryptedCharField(max_length=500)
    description = EncryptedTextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Diagnoses'

    def __str__(self):
        return f"{self.diagnosis} - {self.patient}"


class Prescription(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prescriptions'
    )
    medication = EncryptedCharField(max_length=500)
    dosage = EncryptedCharField(max_length=500)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    instructions = EncryptedTextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.medication} for {self.patient}"


class VitalSign(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='vital_signs'
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vital_signs_recorded'
    )
    blood_pressure_systolic = models.IntegerField(help_text='Systolic (mmHg)')
    blood_pressure_diastolic = models.IntegerField(help_text='Diastolic (mmHg)')
    pulse_rate = models.IntegerField(help_text='Beats per minute')
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text='Temperature in Celsius'
    )
    respiratory_rate = models.IntegerField(
        null=True,
        blank=True,
        help_text='Breaths per minute'
    )
    notes = EncryptedTextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Vitals for {self.patient} at {self.recorded_at}"

    @property
    def blood_pressure(self):
        return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic} mmHg"
