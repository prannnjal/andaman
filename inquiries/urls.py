from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # pre-built views for common authentication tasks like login, password reset etc
from .views import agent_statistics_view

urlpatterns = [
    path('list/', views.inquiry_list, name='inquiry_list'),
    path('follow_up_management/', views.follow_up_management, name='follow_up_management'),
    path('add_inquiry/', views.add_inquiry, name='add_inquiry'),
    path('get_panchayats/', views.get_panchayats, name='get_panchayats'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/inquiries', views.export_inquiries_excel,name='export_inquiries_csv'),
    path('export/users', views.export_users_excel, name='export_users_csv'),
    path('detailed_stats/', views.detailed_stats, name='detailed_stats'),
    path('inquiries_updated_today/', views.inquiries_updated_today_view, name='inquiries_updated_today'),
    
    path('reassign_lead/', views.assign_lead_to_agent_view, name='assign_lead'),
    # ====================================================================================
    
    path('update_status/<int:inquiry_id>/', views.manage_lead_status, name='update_status'),
    path('lead_logs/<int:lead_id>/', views.lead_logs_view, name='view-lead-logs'),
    path('delete_inquiry/<int:id>/', views.delete_inquiry, name='delete_inquiry'),
    
    # ====================================================================================
    path('school_users_list/', views.school_users_list_view, name='school_users_list'),
    
    path('update_school_user/', views.update_school_user_view, name='update_school_user'),
    
    path('delete_school_user/<int:user_id>/', views.delete_school_user_view, name='delete_school_user'),
    # ====================================================================================
    path('login/', views.agent_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),    
    
    # ====================================================================================
    path('add_user/', views.add_user, name='add_user'),
    
    # ====================================================================================
    path('password-reset/', views.password_reset_request, name='password_reset_request'), # Displays the "Enter your email" form to reset password.
    
    
    path('reset/<uidb64>/<token>/', views.set_new_password, name='set_new_password'),  
    # The link sent via email redirects here, where users enter a new password. uidb64:  base64-encoded version of the user's primary key.
    
    # <token>: It ensures that the password reset link is valid and hasn't been tampered with. It verifies that the person clicking the link is authorized to reset the password for that account.
    
    
    # urls.py
    path('filter_inquiries_component/', views.filter_inquiries_component, name='filter_inquiries_component'),
    
    path('hide_columns_component/', views.hide_columns_component, name='hide_columns_component'),
    
    path('hide_agent_columns_component/', views.hide_agent_columns_component, name='hide_agent_columns_component'),
    
    path('filter_agents_component/', views.filter_agents_component, name='filter_agents_component'),
    
    path('bulk_assign_leads/<int:agent_id>/', views.bulk_assign_leads_view, name='bulk_assign_leads'),
    
    path('auto_assign_unassigned_leads/', views.auto_assign_unassigned_leads_view, name='auto_assign_unassigned_leads'),
    
    path('log-call/', views.log_call_view, name='log_call'),
    
    path('transfer-lead/<int:lead_id>/', views.transfer_lead_view, name='transfer_lead'),

    # Call Recording API endpoints
    path('api/lead/<int:lead_id>/recordings/', views.lead_recordings_api, name='lead_recordings_api'),
    path('api/recording/<int:recording_id>/delete/', views.delete_recording_api, name='delete_recording_api'),

    # Call Duration Analytics
    path('call-duration-analytics/', views.call_duration_analytics_view, name='call_duration_analytics'),

    # ====================================================================================
    # Google Sheets Integration URLs
    # ====================================================================================
    path('google-sheets/setup/', views.google_sheets_setup_view, name='google_sheets_setup'),
    path('google-sheets/preview/', views.google_sheets_preview_view, name='google_sheets_preview'),
    path('google-sheets/import/', views.google_sheets_import_view, name='google_sheets_import'),

]
urlpatterns += [
    path('agent/statistics/', agent_statistics_view, name='agent_statistics'),
]