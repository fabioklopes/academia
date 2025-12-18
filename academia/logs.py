from .models import Log

def create_log(user, action):
    """
    Cria um registro de log para uma ação do usuário.
    """
    Log.objects.create(user=user, action=action)
