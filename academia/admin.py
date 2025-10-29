from django.contrib import admin
from .models import User, Group_Role, Class, AttendenceRequest

admin.site.register(User)
admin.site.register(Group_Role)
admin.site.register(Class)
admin.site.register(AttendenceRequest)
