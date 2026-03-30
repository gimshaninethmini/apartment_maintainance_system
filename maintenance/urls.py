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
    
    # NEW URL for request detail
    path('request/<int:request_id>/', views.request_detail_view, name='request_detail'),
]
