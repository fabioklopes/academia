from django.contrib import admin
from .models import User, Class, AttendanceRequest

admin.site.register(User)
admin.site.register(Class)
admin.site.register(AttendanceRequest)
