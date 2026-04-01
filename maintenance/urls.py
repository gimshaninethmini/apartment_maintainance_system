path('manager/request/<int:request_id>/', views.manager_request_detail_view, name='manager_request_detail'),
path('manager/update/<int:request_id>/', views.manager_update_status_view, name='manager_update_status'),
path('export/requests/', views.export_requests_csv, name='export_requests'),