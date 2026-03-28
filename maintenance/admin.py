from django.contrib import admin

from django.contrib import admin
from .models import UserProfile, MaintenanceRequest, Assignment, UpdateLog

admin.site.register(UserProfile)
admin.site.register(MaintenanceRequest)
admin.site.register(Assignment)
admin.site.register(UpdateLog)
