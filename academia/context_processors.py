from .models import User

def account_management_context(request):
    context = {}
    if request.user.is_authenticated:
        original_user_id = request.session.get('original_user_id')
        main_user = None
        
        if original_user_id:
            # User is logged in as a dependent
            try:
                main_user = User.objects.get(id=original_user_id)
            except User.DoesNotExist:
                # If the original user is gone, clear the session key
                request.session.pop('original_user_id', None)
        else:
            # User is logged in as the main account holder
            main_user = request.user

        dependents = main_user.dependents.all() if main_user and main_user.dependents.exists() else []

        context = {
            'original_user_id': original_user_id,
            'dependents_list': dependents,
        }
            
    return context
