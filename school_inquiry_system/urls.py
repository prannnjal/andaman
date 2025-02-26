from django.contrib import admin
from django.urls import path, include, reverse_lazy
'''
path → Used to define URL patterns.
include → Allows including URL configurations from other apps.
reverse_lazy → Used to generate a URL for the dashboard view dynamically.
'''
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect(reverse_lazy('dashboard'), permanent=True)),  # When a user visits / (the root of the site), they are automatically redirected to 'dashboard'. 
    
    # reverse_lazy('dashboard'): Finds the URL that has the name 'dashboard' in your urls.py
    
    path('admin/', admin.site.urls),    # This enables Django's admin interface at /admin/.
    path('inquiries/', include('inquiries.urls')),  # This tells Django to look inside inquiries/urls.py for more URL patterns.
]
