from django.contrib import admin
from .models import ClinicalNote, Diagnosis, Prescription, VitalSign


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'created_at')
    list_filter = ('doctor', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'note')


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('patient', 'diagnosis', 'doctor', 'created_at')
    list_filter = ('doctor', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'diagnosis')


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medication', 'dosage', 'doctor', 'created_at')
    list_filter = ('doctor', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'medication')


@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ('patient', 'blood_pressure', 'pulse_rate', 'recorded_by', 'recorded_at')
    list_filter = ('recorded_by', 'recorded_at')
    search_fields = ('patient__first_name', 'patient__last_name')
