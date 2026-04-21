from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile, MaintenanceRequest, Assignment, UpdateLog
from django.http import HttpResponseForbidden, HttpResponse
from django.core.paginator import Paginator
import csv

# ========== AUTHENTICATION VIEWS ==========
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
        
        # Check password length (minimum 6 characters)
        if len(password1) < 6:
            messages.error(request, '❌ Password must be at least 6 characters long.')
            return redirect('register')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, '❌ Username already exists. Please choose a different username.')
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
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            # Check if username exists
            if User.objects.filter(username=username).exists():
                messages.error(request, '❌ Incorrect Username or password. Please try again.')
            else:
                messages.error(request, '❌ Incorrect Username or password. Please try again.')
            return redirect('login')
    
    # GET request - just show empty login form, no messages
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ========== DASHBOARD VIEW ==========
@login_required
def dashboard_view(request):
    profile = request.user.userprofile
    
    if profile.role == 'tenant':
        requests = MaintenanceRequest.objects.filter(tenant=request.user).order_by('-created_at')
        paginator = Paginator(requests, 5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'maintenance/tenant_dashboard.html', {'requests': page_obj})
    
    elif profile.role == 'manager':
        all_requests = MaintenanceRequest.objects.all().order_by('-created_at')
        
        total_requests = all_requests.count()
        pending_count = all_requests.filter(status='submitted').count()
        assigned_count = all_requests.filter(status='assigned').count()
        in_progress_count = all_requests.filter(status='in_progress').count()
        completed_count = all_requests.filter(status='completed').count()
        
        technicians = User.objects.filter(userprofile__role='technician')
        
        paginator = Paginator(all_requests, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'maintenance/manager_dashboard.html', {
            'requests': page_obj,
            'technicians': technicians,
            'total_requests': total_requests,
            'pending_count': pending_count,
            'assigned_count': assigned_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
        })
    
    elif profile.role == 'technician':
        assignments = Assignment.objects.filter(technician=request.user)
        return render(request, 'maintenance/technician_dashboard.html', {'assignments': assignments})
    
    return HttpResponseForbidden("Invalid role")

# ========== TENANT VIEWS ==========
@login_required
def submit_request_view(request):
    if request.user.userprofile.role != 'tenant':
        return HttpResponseForbidden("Only tenants can submit requests")
    
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        priority = request.POST['priority']
        image = request.FILES.get('image')
        
        request_obj = MaintenanceRequest.objects.create(
            tenant=request.user,
            title=title,
            description=description,
            priority=priority,
            image=image
        )
        
        UpdateLog.objects.create(
            request=request_obj,
            updated_by=request.user,
            status='submitted',
            notes='Request submitted by tenant'
        )
        
        messages.success(request, 'Request submitted successfully!')
        return redirect('dashboard')
    
    return render(request, 'maintenance/submit_request.html')

@login_required
def request_detail_view(request, request_id):
    if request.user.userprofile.role != 'tenant':
        return HttpResponseForbidden("Only tenants can view request details")
    
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id, tenant=request.user)
    return render(request, 'maintenance/request_detail.html', {'request': maintenance_request})

@login_required
def edit_request_view(request, request_id):
    if request.user.userprofile.role != 'tenant':
        return HttpResponseForbidden("Only tenants can edit requests")
    
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id, tenant=request.user)
    
    if maintenance_request.status != 'submitted':
        messages.error(request, 'Only pending requests can be edited')
        return redirect('dashboard')
    
    if request.method == 'POST':
        maintenance_request.title = request.POST['title']
        maintenance_request.description = request.POST['description']
        maintenance_request.priority = request.POST['priority']
        maintenance_request.save()
        
        messages.success(request, 'Request updated successfully!')
        return redirect('request_detail', request_id=maintenance_request.id)
    
    return render(request, 'maintenance/edit_request.html', {'request': maintenance_request})

@login_required
def cancel_request_view(request, request_id):
    if request.user.userprofile.role != 'tenant':
        return HttpResponseForbidden("Only tenants can cancel requests")
    
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id, tenant=request.user)
    
    if maintenance_request.status != 'submitted':
        messages.error(request, 'Only pending requests can be cancelled')
        return redirect('dashboard')
    
    maintenance_request.status = 'cancelled'
    maintenance_request.save()
    
    messages.success(request, 'Request cancelled successfully!')
    return redirect('dashboard')

# ========== MANAGER VIEWS ==========
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
def manager_request_detail_view(request, request_id):
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can view this page")
    
    maintenance_request = MaintenanceRequest.objects.get(id=request_id)
    technicians = User.objects.filter(userprofile__role='technician')
    
    return render(request, 'maintenance/manager_request_detail.html', {
        'request': maintenance_request,
        'technicians': technicians
    })

@login_required
def manager_update_status_view(request, request_id):
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can update status")
    
    if request.method == 'POST':
        maintenance_request = MaintenanceRequest.objects.get(id=request_id)
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        maintenance_request.status = new_status
        maintenance_request.save()
        
        UpdateLog.objects.create(
            request=maintenance_request,
            updated_by=request.user,
            status=new_status,
            notes=notes
        )
        
        messages.success(request, f'Status updated to {new_status}')
    
    return redirect('manager_request_detail', request_id=request_id)

@login_required
def export_requests_csv(request):
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can export data")
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="maintenance_requests.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Tenant', 'Apartment', 'Priority', 'Status', 'Submitted Date', 'Description'])
    
    requests = MaintenanceRequest.objects.all().order_by('-created_at')
    
    for req in requests:
        writer.writerow([
            req.id,
            req.title,
            req.tenant.username,
            req.tenant.userprofile.apartment_number or 'N/A',
            req.priority,
            req.status,
            req.created_at.strftime('%Y-%m-%d %H:%M'),
            req.description
        ])
    
    return response

# ========== TECHNICIAN VIEWS ==========
@login_required
def update_status_view(request, request_id):
    if request.user.userprofile.role != 'technician':
        return HttpResponseForbidden("Only technicians can update status")
    
    assignment = get_object_or_404(Assignment, request_id=request_id, technician=request.user)
    
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