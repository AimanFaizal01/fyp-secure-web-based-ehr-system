from django.db import migrations
from django.contrib.postgres.operations import CryptoExtension

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_user_mfa_exempt'), # Link to latest accounts migration
    ]

    operations = [
        CryptoExtension(),
    ]
