from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # pre-built views for common authentication tasks like login, password reset etc

urlpatterns = [
    path('list/', views.inquiry_list, name='inquiry_list'),
    path('add_inquiry/', views.add_inquiry, name='add_inquiry'),
    path('get_panchayats/', views.get_panchayats, name='get_panchayats'),
    path('agents_performance/', views.agent_performance, name='agent_performance'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/', views.export_inquiries_excel,name='export_inquiries_csv'),
    path('remove_lead/', views.remove_lead_from_agent_view, name='remove_lead'),
    path('reassign_lead/', views.assign_lead_to_agent_view, name='assign_lead'),        
    path('update_status/<int:inquiry_id>/', views.manage_lead_status, name='update_status'),
    path('delete_inquiry/<int:id>/', views.delete_inquiry, name='delete_inquiry'),
    
    path('agents/', views.agent_list, name='agent_list'),
    path('agents/add/', views.add_agent, name='add_agent'),
    
    path('login/', views.agent_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'), # Displays the "Enter your email" form to reset password.
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),   # The PasswordResetDoneView displays a page informing the user that an email has been sent (if the email is registered).
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),  
    # The link sent via email redirects here, where users enter a new password. uidb64:  base64-encoded version of the user's primary key.
    
    # <token>: It ensures that the password reset link is valid and hasn't been tampered with. It verifies that the person clicking the link is authorized to reset the password for that account.
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),    # Displays a success message after password reset is completed.
]