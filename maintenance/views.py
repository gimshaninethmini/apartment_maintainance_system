from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile, MaintenanceRequest, Assignment, UpdateLog
from django.http import HttpResponseForbidden, HttpResponse
from django.db.models import Count, Q
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
        
        user = User.objects.create_user(username=username, password=password1)
        profile = user.userprofile
        profile.role = role
        profile.apartment_number = apartment_number
        if role == 'manager':
            profile.manager_approved = False
            user.is_active           = False
            user.save()
            profile.save()
            messages.info(
                request,
                'Your manager account request has been submitted. '
                'Please wait for admin approval before logging in.'
            )
            return redirect('login')
        profile.save()
        
        login(request, user)
        return redirect('dashboard')
    
    return render(request, 'maintenance/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # ================================================================
        # MANAGER APPROVAL CHECK - Check BEFORE authentication
        # ================================================================
        try:
            pending_user = User.objects.get(username=username)
            if (hasattr(pending_user, 'userprofile') and
                    pending_user.userprofile.role == 'manager' and
                    pending_user.userprofile.manager_approved is False):
                messages.error(
                    request,
                    'Your manager account is pending admin approval. '
                    'Please check back later.'
                )
                return render(request, 'registration/login.html')
        except User.DoesNotExist:
            pass
        
        # Normal authentication
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
   
    # Start with all requests ordered by newest first
        all_requests = MaintenanceRequest.objects.all().order_by('-created_at')
    
    # Search functionality
        search = request.GET.get('search', '').strip()
        if search:
            all_requests = all_requests.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tenant__username__icontains=search)
            )
    
    # Status filter
        status_filter = request.GET.get('status', '')
        if status_filter:
            all_requests = all_requests.filter(status=status_filter)
    
    # Priority filter
        priority_filter = request.GET.get('priority', '')
        if priority_filter:
            all_requests = all_requests.filter(priority=priority_filter)
    
    # Statistics counts - from full dataset (unfiltered)
        all_qs = MaintenanceRequest.objects.all()
        total_count = all_qs.count()
        pending_count = all_qs.filter(status='submitted').count()
        reviewed_count = all_qs.filter(status='reviewed').count()
        assigned_count = all_qs.filter(status='assigned').count()
        in_progress_count = all_qs.filter(status='in_progress').count()
        completed_count = all_qs.filter(status='completed').count()
        cancelled_count = all_qs.filter(status='cancelled').count()
    
    # Technicians with active task counts
        technicians = User.objects.filter(
            userprofile__role='technician'
        ).annotate(
            active_tasks=Count(
                'assignment',
                filter=Q(assignment__request__status__in=['assigned', 'in_progress'])
            )
        )
    
    # Pagination (10 per page)
        paginator = Paginator(all_requests, 10)
        page_obj = paginator.get_page(request.GET.get('page'))
    
        return render(request, 'maintenance/manager_dashboard.html', {
            'requests': page_obj,
            'technicians': technicians,
            'total_count': total_count,
            'pending_count': pending_count,
            'reviewed_count': reviewed_count,
            'assigned_count': assigned_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'cancelled_count': cancelled_count,
            'search': search,
            'status_filter': status_filter,
            'priority_filter': priority_filter,
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

#  ========== NEW MANAGER VIEWS ==========

@login_required
def chart_data_view(request):
    """JSON endpoint — feeds real data to the manager dashboard chart."""
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden()

    qs = MaintenanceRequest.objects.all()
    data = {
        'labels': ['Submitted', 'Reviewed', 'Assigned', 'In Progress', 'Completed', 'Cancelled'],
        'values': [
            qs.filter(status='submitted').count(),
            qs.filter(status='reviewed').count(),
            qs.filter(status='assigned').count(),
            qs.filter(status='in_progress').count(),
            qs.filter(status='completed').count(),
            qs.filter(status='cancelled').count(),
        ],
        'colors': ['#6B7280', '#3B82F6', '#F59E0B', '#7C3AED', '#16A34A', '#EF4444'],
    }
    return JsonResponse(data)


@login_required
def manager_request_detail_view(request, request_id):
    """Full detail page for a single request — manager view."""
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can view this page.")

    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    # Technicians with their current active task count shown
    technicians = User.objects.filter(
        userprofile__role='technician'
    ).annotate(
        active_tasks=Count(
            'assignment',
            filter=Q(assignment__request__status__in=['assigned', 'in_progress'])
        )
    )

    logs = maintenance_request.logs.order_by('created_at')

    # Get existing assignment if any
    try:
        existing_assignment = maintenance_request.assignment
    except Assignment.DoesNotExist:
        existing_assignment = None

    return render(request, 'maintenance/manager_request_detail.html', {
        'request':             maintenance_request,
        'technicians':         technicians,
        'logs':                logs,
        'existing_assignment': existing_assignment,
    })


@login_required
def assign_technician_view(request, request_id):
    """Assign or re-assign a technician to a request."""
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can assign technicians.")

    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    if request.method == 'POST':
        technician_id = request.POST.get('technician_id')

        if not technician_id:
            messages.error(request, 'Please select a technician.')
            return redirect('manager_request_detail', request_id=request_id)

        try:
            technician = User.objects.get(
                id=technician_id,
                userprofile__role='technician'
            )
        except User.DoesNotExist:
            messages.error(request, 'Selected technician not found.')
            return redirect('manager_request_detail', request_id=request_id)

        # update_or_create fixes the OneToOne crash on re-assign
        Assignment.objects.update_or_create(
            request=maintenance_request,
            defaults={
                'technician': technician,
                'notes':      request.POST.get('notes', ''),
            }
        )

        maintenance_request.status = 'assigned'
        maintenance_request.save()

        UpdateLog.objects.create(
            request=maintenance_request,
            updated_by=request.user,
            status='assigned',
            notes=f'Assigned to {technician.username}. {request.POST.get("notes", "")}',
        )

        messages.success(request, f'Request assigned to {technician.username}.')
        return redirect('manager_request_detail', request_id=request_id)

    return redirect('dashboard')


@login_required
def manager_update_status_view(request, request_id):
    """Manager updates the status of a request with validation."""
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can update status.")

    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)

    # Valid status flow — prevents going backwards
    VALID_TRANSITIONS = {
        'submitted':   ['reviewed', 'cancelled'],
        'reviewed':    ['assigned', 'cancelled'],
        'assigned':    ['in_progress', 'cancelled'],
        'in_progress': ['completed'],
        'completed':   [],
        'cancelled':   [],
    }

    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes      = request.POST.get('notes', '')

        allowed = VALID_TRANSITIONS.get(maintenance_request.status, [])
        if new_status not in allowed:
            messages.error(
                request,
                f'Cannot change status from '
                f'"{maintenance_request.status}" to "{new_status}".'
            )
            return redirect('manager_request_detail', request_id=request_id)

        maintenance_request.status = new_status
        maintenance_request.save()

        UpdateLog.objects.create(
            request=maintenance_request,
            updated_by=request.user,
            status=new_status,
            notes=notes,
        )

        messages.success(request, f'Status updated to {new_status}.')

    return redirect('manager_request_detail', request_id=request_id)


@login_required
def export_requests_csv(request):
    """Export all requests as CSV — optional status filter via ?status="""
    if request.user.userprofile.role != 'manager':
        return HttpResponseForbidden("Only managers can export data.")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="maintenance_requests.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Tenant', 'Apartment',
        'Priority', 'Status', 'Submitted Date', 'Description'
    ])

    qs = MaintenanceRequest.objects.all().order_by('-created_at')

    # Optional status filter on export
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    for req in qs:
        writer.writerow([
            req.id,
            req.title,
            req.tenant.username,
            req.tenant.userprofile.apartment_number or 'N/A',
            req.priority,
            req.status,
            req.created_at.strftime('%Y-%m-%d %H:%M'),
            req.description,
        ])

    return response