from django.contrib.auth.backends import ModelBackend
from .models import User

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, access_group=None, **kwargs):
        try:
            user = User.objects.get(email=email, group_role=access_group)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
