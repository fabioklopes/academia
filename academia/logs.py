from .models import Log, User

def create_log(user, action, status='SUCESSO', first_name=None, email=None):
    """
    Cria um registro de log para uma ação.
    """
    # Ignore status, first_name and email arguments since model doesn't support them
    Log.objects.create(
        user=user if isinstance(user, User) else None,
        action=action
    )
