from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from maintenance import views

urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False)),
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Tenant URLs
    path('submit/', views.submit_request_view, name='submit_request'),
    path('request/<int:request_id>/', views.request_detail_view, name='request_detail'),
    path('request/<int:request_id>/edit/', views.edit_request_view, name='edit_request'),
    path('request/<int:request_id>/cancel/', views.cancel_request_view, name='cancel_request'),
    
    # Manager URLs
    path('manager/assign/<int:request_id>/', views.assign_technician_view, name='assign_technician'),
    path('manager/request/<int:request_id>/', views.manager_request_detail_view, name='manager_request_detail'),
    path('manager/status/<int:request_id>/', views.manager_update_status_view, name='manager_update_status'),
    path('manager/export/', views.export_requests_csv, name='export_requests_csv'),
    path('manager/chart-data/', views.chart_data_view, name='chart_data'),
    
    # Technician URLs
    # Technician URLs
    path('update/<int:request_id>/', views.update_status_view, name='update_status'),
<<<<<<< HEAD
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
=======
    
    # Profile URL
    path('profile/', views.profile_view, name='profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
>>>>>>> testing-module
