from django.contrib import admin
from .models import Lead, CustomUser, School

admin.site.register(Lead)
admin.site.register(CustomUser)
admin.site.register(School)