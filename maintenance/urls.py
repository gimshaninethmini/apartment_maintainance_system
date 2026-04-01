from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('submit/', views.submit_request_view, name='submit_request'),
    path('assign/<int:request_id>/', views.assign_technician_view, name='assign_technician'),
    path('update/<int:request_id>/', views.update_status_view, name='update_status'),
    path('logout/', views.logout_view, name='logout'),
    path('request/<int:request_id>/', views.request_detail_view, name='request_detail'),
    path('request/<int:request_id>/edit/', views.edit_request_view, name='edit_request'),
    path('request/<int:request_id>/cancel/', views.cancel_request_view, name='cancel_request'),
    path('manager/request/<int:request_id>/', views.manager_request_detail_view, name='manager_request_detail'),
    path('manager/update/<int:request_id>/', views.manager_update_status_view, name='manager_update_status'),
    path('export/requests/', views.export_requests_csv, name='export_requests'),
]