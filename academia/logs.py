from .models import Log, User

def create_log(user, action, status='SUCESSO', first_name=None, email=None):
    """
    Cria um registro de log para uma ação.
    """
    if user and isinstance(user, User):
        Log.objects.create(
            user=user,
            first_name=user.first_name,
            email=user.email,
            action=action,
            status=status
        )
    else:
        # For failed logins or system actions where user is not authenticated
        Log.objects.create(
            user=None,
            first_name=first_name,
            email=email,
            action=action,
            status=status
        )
