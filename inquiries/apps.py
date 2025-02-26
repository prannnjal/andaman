from django.apps import AppConfig   # Imports Django's base class for app configurations.


class InquiriesConfig(AppConfig):   # Creates a configuration class for the app.
    name = 'inquiries'  # Tells Django that this app is identified by the name "inquiries". Django uses this name to locate the app and its resources (models, views, templates, etc.).
