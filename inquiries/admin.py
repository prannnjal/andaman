from django.contrib import admin
from .models import Lead, CustomUser, School, CompanySettings

admin.site.register(Lead)
admin.site.register(CustomUser)
admin.site.register(School)
admin.site.register(CompanySettings)