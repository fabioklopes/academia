from .models import AttendanceRequest, Graduacao, User

def notifications_context(request):
    """
    Fornece notificações para o sistema de toast.
    """
    # Se o usuário não estiver ativo, não contabilizar os Toasters (notificações)
    if not request.user.is_active:
        return {}

    notifications = []
    
    # Notificações para Alunos
    if request.user.is_student():
        # Presenças aprovadas
        approved_attendances = AttendanceRequest.objects.filter(student=request.user, status='APR', notified=False)
        if approved_attendances.exists():
            count = approved_attendances.count()
            notifications.append({
                'text': f'{count} presença(s) aprovada(s).',
                'url': 'aluno_presencas'
            })

        # Graduações novas
        new_graduations = Graduacao.objects.filter(aluno=request.user, notified=False)
        if new_graduations.exists():
            notifications.append({
                'text': 'Você tem uma nova graduação!',
                'url': 'aluno_graduacoes'
            })

    # Notificações para Professores e Administradores
    if request.user.is_professor_or_admin():
        # Solicitações de presença pendentes
        pending_attendances = AttendanceRequest.objects.filter(status='PEN')
        
        if pending_attendances.exists():
            count = pending_attendances.count()
            notifications.append({
                'text': f'{count} solicitação(ões) de presença pendente(s).',
                'url': 'professor_presencas'
            })

        # Novos usuários pendentes de aprovação
        pending_users = User.objects.filter(status='PENDENTE') # Alterado de is_active=False para status='PENDENTE'
        if pending_users.exists():
            count = pending_users.count()
            notifications.append({
                'text': f'{count} novo(s) usuário(s) aguardando aprovação.',
                'url': 'professor_alunos'
            })

    if notifications:
        return {'notifications': notifications, 'has_pending_tasks': True}
        
    return {}

def account_management_context(request):
    original_user_id = request.session.get('original_user_id')
    main_user = None
    
    if original_user_id:
        try:
            main_user = User.objects.get(id=original_user_id)
        except User.DoesNotExist:
            request.session.pop('original_user_id', None)
    else:
        main_user = request.user

    dependents = main_user.dependents.all() if main_user and main_user.dependents.exists() else []

    return {
        'original_user_id': original_user_id,
        'dependents_list': dependents,
    }

def global_context(request):
    """
    Combina todos os processadores de contexto personalizados.
    """
    if not request.user.is_authenticated:
        return {}

    context = {}
    context.update(notifications_context(request))
    context.update(account_management_context(request))
    return context
