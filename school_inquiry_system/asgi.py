"""
ASGI config for school_inquiry_system project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application   # his function creates and returns an ASGI application instance, which is necessary for handling asynchronous requests in Django.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_inquiry_system.settings')

application = get_asgi_application()        # application is a callable object that ASGI servers (like Daphne or Uvicorn) use to serve the Django application.


'''
Why is ASGI Important?
Unlike WSGI (which only supports synchronous requests), ASGI supports:
WebSockets (real-time communication)
Long-lived connections
Background tasks
Async frameworks (like FastAPI
'''