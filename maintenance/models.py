from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    USER_ROLES = (
        ('tenant', 'Tenant'),
        ('manager', 'Property Manager'),
        ('technician', 'Technician'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='tenant')
    phone = models.CharField(max_length=15, blank=True)
    apartment_number = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class MaintenanceRequest(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    )
    
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='issues/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.tenant.username}"

class Assignment(models.Model):
    request = models.OneToOneField(MaintenanceRequest, on_delete=models.CASCADE)
    technician = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'userprofile__role': 'technician'})
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.request.title} assigned to {self.technician.username}"

class UpdateLog(models.Model):
    request = models.ForeignKey(MaintenanceRequest, on_delete=models.CASCADE, related_name='logs')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.request.title} - {self.status} by {self.updated_by.username}"