import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from django.db import models
from django.conf import settings

class EncryptionService:
    @staticmethod
    def get_key():
        secret_key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
        if not secret_key:
            raise ValueError("FIELD_ENCRYPTION_KEY is not set in settings.py")
        
        # Ensure we generate a clean 256-bit key derive
        salt = b'\x00' * 16  # Using fixed determinism for the field salt derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(secret_key.encode())

    @classmethod
    def encrypt(cls, value):
        if not value:
            return value
        
        key = cls.get_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12) # Standard 12-byte nonce for GCM
        
        ciphertext = aesgcm.encrypt(nonce, value.encode(), None)
        
        # Package nonce + ciphertext to base64 representation for database storage
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode('utf-8')

    @classmethod
    def decrypt(cls, value):
        if not value:
            return value
        
        try:
            key = cls.get_key()
            aesgcm = AESGCM(key)
            
            raw_data = base64.b64decode(value.encode('utf-8'))
            nonce = raw_data[:12]
            ciphertext = raw_data[12:]
            
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted.decode('utf-8')
        except Exception:
            # Graceful fallback for existing unencrypted/legacy data
            return value

class EncryptedCharField(models.CharField):
    """
    A field that automatically encrypts and decrypts its content.
    """
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return EncryptionService.encrypt(value)

    def from_db_value(self, value, expression, connection):
        return EncryptionService.decrypt(value)

    def to_python(self, value):
        if value is None:
            return value
        return EncryptionService.decrypt(value)

class EncryptedTextField(models.TextField):
    """
    A text field that automatically encrypts and decrypts its content.
    """
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return EncryptionService.encrypt(value)

    def from_db_value(self, value, expression, connection):
        return EncryptionService.decrypt(value)

    def to_python(self, value):
        if value is None:
            return value
        return EncryptionService.decrypt(value)
