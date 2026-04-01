from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile, MaintenanceRequest, Assignment, UpdateLog
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        role = request.POST['role']
        apartment_number = request.POST.get('apartment_number', '')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')
        
        user = User.objects.create_user(username=username, password=password1)
        profile = user.userprofile
        profile.role = role
        profile.apartment_number = apartment_number
        profile.save()
        
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'maintenance/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    profile = request.user.userprofile
    
    if profile.role == 'tenant':
        requests = MaintenanceRequest.objects.filter(tenant=request.user)
        return render(request, 'maintenance/tenant_dashboard.html', {'requests': requests})
    
    elif profile.role == 'manager':
      from django.db.models import Q, Count
    
      # Get all requests
      all_requests = MaintenanceRequest.objects.all().order_by('-created_at')
    
      # Calculate counts for statistics
      total_requests = all_requests.count()
      pending_count = all_requests.filter(status='submitted').count()
      assigned_count = all_requests.filter(status='assigned').count()
      completed_count = all_requests.filter(status='completed').count()
    
      # Get all technicians for assignment dropdown
      technicians = User.objects.filter(userprofile__role='technician')
    
      # Add pagination
      paginator = Paginator(all_requests, 10)  # 10 per page
      page_number = request.GET.get('page')
      page_obj = paginator.get_page(page_number)
    
      return render(request, 'maintenance/manager_dashboard.html', {
        'requests': page_obj,
        'technicians': technicians,
        'total_requests': total_requests,
        'pending_count': pending_count,
        'assigned_count': assigned_count,
        'completed_count': completed_count,
      })
    
    elif profile.role == 'technician':
        assignments = Assignment.objects.filter(technician=request.user)
        return render(request, 'maintenance/technician_dashboard.html', {'assignments': assignments})
    
    return HttpResponseForbidden("Invalid role")

@login_required
def submit_request_view(request):
    if request.user.userprofile.role != 'tenant':
        return HttpResponseForbidden("Only tenants can submit requests")
    
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        priority = request.POST['priority']
        
        request_obj = MaintenanceRequest.objects.create(
            tenant=request.user,
            title=title,
            description=description,
            priority=priority
        )
        
        messages.success(request, 'Request submitted successfully!')
        return redirect('dashboard')
    
    return render(request, 'maintenance/submit_request.html')

@login_required
def assign_technician_view(request, request_id):
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can assign technicians")
    
    if request.method == 'POST':
        technician_id = request.POST['technician_id']
        technician = User.objects.get(id=technician_id)
        maintenance_request = MaintenanceRequest.objects.get(id=request_id)
        
        assignment = Assignment.objects.create(
            request=maintenance_request,
            technician=technician,
            notes=request.POST.get('notes', '')
        )
        
        maintenance_request.status = 'assigned'
        maintenance_request.save()
        
        messages.success(request, f'Request assigned to {technician.username}')
        return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def update_status_view(request, request_id):
    if request.user.userprofile.role != 'technician':
        return HttpResponseForbidden("Only technicians can update status")
    
    assignment = Assignment.objects.get(request_id=request_id, technician=request.user)
    
    if request.method == 'POST':
        new_status = request.POST['status']
        notes = request.POST.get('notes', '')
        
        assignment.request.status = new_status
        assignment.request.save()
        
        UpdateLog.objects.create(
            request=assignment.request,
            updated_by=request.user,
            status=new_status,
            notes=notes
        )
        
        messages.success(request, f'Status updated to {new_status}')
        return redirect('dashboard')
    
    return render(request, 'maintenance/update_status.html', {'assignment': assignment})

@login_required
def manager_request_detail_view(request, request_id):
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can view this page")
    
    maintenance_request = MaintenanceRequest.objects.get(id=request_id)
    technicians = User.objects.filter(userprofile__role='technician')
    
    return render(request, 'maintenance/manager_request_detail.html', {
        'request': maintenance_request,
        'technicians': technicians
    })