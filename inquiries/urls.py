from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # pre-built views for common authentication tasks like login, password reset etc

urlpatterns = [
    path('list/', views.inquiry_list, name='inquiry_list'),
    path('follow_up_management/', views.follow_up_management, name='follow_up_management'),
    path('add_inquiry/', views.add_inquiry, name='add_inquiry'),
    path('get_panchayats/', views.get_panchayats, name='get_panchayats'),
    path('agents_performance/', views.agent_performance, name='agent_performance'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/inquiries', views.export_inquiries_excel,name='export_inquiries_csv'),
    path('export/users', views.export_users_excel, name='export_users_csv'),
    path('detailed_stats/', views.detailed_stats, name='detailed_stats'),
    path('remove_lead/', views.remove_lead_from_agent_view, name='remove_lead'),
    path('reassign_lead/', views.assign_lead_to_agent_view, name='assign_lead'),        
    path('update_status/<int:inquiry_id>/', views.manage_lead_status, name='update_status'),
    path('lead_logs/<int:lead_id>/', views.lead_logs_view, name='view-lead-logs'),
    path('delete_inquiry/<int:id>/', views.delete_inquiry, name='delete_inquiry'),
    
    
    path('agents/', views.agent_list, name='agent_list'),
    path('agents/add/', views.add_agent, name='add_agent'),
    path('manage_access/', views.manage_access, name='manage_access'),
    
    path('login/', views.agent_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),    
    
    
    path('add_user/', views.add_user, name='add_user'),
    
    
    path('password-reset/', views.password_reset_request, name='password_reset_request'), # Displays the "Enter your email" form to reset password.
    
    
    path('reset/<uidb64>/<token>/', views.set_new_password, name='set_new_password'),  
    # The link sent via email redirects here, where users enter a new password. uidb64:  base64-encoded version of the user's primary key.
    
    # <token>: It ensures that the password reset link is valid and hasn't been tampered with. It verifies that the person clicking the link is authorized to reset the password for that account.
    
    
    # urls.py
    path('filter_inquiries_component/', views.filter_inquiries_component, name='filter_inquiries_component'),
    
    path('hide_columns_component/', views.hide_columns_component, name='hide_columns_component'),

]