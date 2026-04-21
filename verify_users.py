#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apartmentsystem.settings')
django.setup()

from django.contrib.auth.models import User

print("=" * 60)
print("✅ LOGIN CREDENTIALS FOR TEST ACCOUNTS")
print("=" * 60)
print()

# Define the actual passwords set during creation
passwords = {
    'admin': 'admin123',
    'tenant1': 'tenant123',
    'tech1': 'tech123',
    'manager1': 'manager123'
}

for user in User.objects.all().order_by('username'):
    profile = user.userprofile if hasattr(user, 'userprofile') else None
    role = profile.role if profile else 'N/A'
    password = passwords.get(user.username, user.username + '123')
    
    # Verify password
    is_valid = user.check_password(password)
    status = "✅" if is_valid else "❌"
    
    print(f"{status} Username: {user.username:15} | Password: {password:15} | Role: {role}")

print()
print("=" * 60)
print("Ready to login! Use the credentials above.")
print("=" * 60)
