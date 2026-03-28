from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from maintenance import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('submit/', views.submit_request_view, name='submit_request'),
    path('assign/<int:request_id>/', views.assign_technician_view, name='assign_technician'),
    path('update/<int:request_id>/', views.update_status_view, name='update_status'),
    path('logout/', views.logout_view, name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)