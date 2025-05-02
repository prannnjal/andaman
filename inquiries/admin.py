from django.contrib import admin
from .models import Lead, CustomUser

admin.site.register(Lead)
admin.site.register(CustomUser)