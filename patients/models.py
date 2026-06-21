from django.db import models
from django.conf import settings
from config.encryption import EncryptedCharField, EncryptedTextField

class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        COMPLETED = 'completed', 'Completed'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    # Using AES-256 encryption for PII
    first_name = EncryptedCharField(max_length=500)
    last_name = EncryptedCharField(max_length=500, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True, null=True)
    phone = EncryptedCharField(max_length=500, blank=True, null=True)
    email = EncryptedCharField(max_length=500, blank=True)
    address = EncryptedTextField(blank=True)
    emergency_contact_name = EncryptedCharField(max_length=500, blank=True)
    emergency_contact_phone = EncryptedCharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='patients_created'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
