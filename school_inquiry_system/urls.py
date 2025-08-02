from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inquiries/', include('inquiries.urls')),
    path('', RedirectView.as_view(url='/inquiries/dashboard/', permanent=False)),  # Redirects users who visit the root of the site), they are automatically redirected to 'dashboard'.
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
