from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from config.encryption import EncryptedCharField, EncryptedTextField

class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # Guarantee the custom hospital role is mapped to master Admin during creation
        extra_fields.setdefault('role', 'admin')
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    objects = CustomUserManager()
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        DOCTOR = 'doctor', 'Doctor'
        NURSE = 'nurse', 'Nurse'
        RECEPTIONIST = 'receptionist', 'Receptionist'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RECEPTIONIST
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    phone = EncryptedCharField(max_length=500, blank=True)
    
    # Security Requirements (#5)
    mfa_enabled = models.BooleanField(default=False)
    mfa_exempt = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    security_risk_level = models.IntegerField(default=0) # 0-100 scale
    is_locked = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    needs_password_change = models.BooleanField(default=False)
    temp_password = EncryptedCharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_receptionist(self):
        return self.role == self.Role.RECEPTIONIST

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_nurse(self):
        return self.role == self.Role.NURSE

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    resource = models.CharField(max_length=100, blank=True)
    resource_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_suspicious = models.BooleanField(default=False)
    details = EncryptedTextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"
