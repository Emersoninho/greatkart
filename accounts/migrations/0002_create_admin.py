from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_admin(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    
    if not Account.objects.filter(email='admin@greatkart.com').exists():
        Account.objects.create(
            first_name='Admin',
            last_name='GreatKart',
            username='admin',
            email='admin@greatkart.com',
            password=make_password('Admin123@'),
            is_staff=True,
            is_superuser=True,
            is_admin=True,
            is_active=True,
        )

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_admin),
    ]