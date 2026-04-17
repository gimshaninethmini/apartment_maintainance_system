#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartmentsystem.settings')
django.setup()

from django.contrib.auth.models import User
from maintenance.models import UserProfile

# Create admin user
admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
print(f"✅ Created admin: admin / admin123")

# Create tenant user
tenant = User.objects.create_user('tenant1', 'tenant1@test.com', 'tenant123')
# Update the auto-created UserProfile
tenant.userprofile.role = 'tenant'
tenant.userprofile.apartment_number = '101'
tenant.userprofile.phone = '555-0101'
tenant.userprofile.save()
print(f"✅ Created tenant: tenant1 / tenant123")

# Create technician user
technician = User.objects.create_user('tech1', 'tech1@test.com', 'tech123')
# Update the auto-created UserProfile
technician.userprofile.role = 'technician'
technician.userprofile.phone = '555-0201'
technician.userprofile.save()
print(f"✅ Created technician: tech1 / tech123")

# Create manager user
manager = User.objects.create_user('manager1', 'manager1@test.com', 'manager123')
# Update the auto-created UserProfile
manager.userprofile.role = 'manager'
manager.userprofile.phone = '555-0301'
manager.userprofile.save()
print(f"✅ Created manager: manager1 / manager123")

# Verify all users
print("\n📋 All Users Created:")
for user in User.objects.all():
    profile = user.userprofile if hasattr(user, 'userprofile') else None
    role = profile.role if profile else 'N/A'
    print(f"  - {user.username} ({role})")
