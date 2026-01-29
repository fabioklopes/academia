from .models import Log, User

def create_log(user, action, status='SUCESSO', **kwargs):
    """
    Cria um registro de log para uma ação.
    """
    Log.objects.create(
        user=user if isinstance(user, User) else None,
        action=action,
        status=status
    )
