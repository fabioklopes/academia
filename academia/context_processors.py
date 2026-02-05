from django.core.exceptions import ObjectDoesNotExist
from .models import AttendanceRequest, Graduacao, User

def notifications_context(request):
    """
    Fornece notificações granulares para o sistema de toasts múltiplos.
    """
    if not request.user.is_active:
        return {}

    notifications = []
    total_count = 0
    user = request.user
    
    # --- NOTIFICAÇÕES DE EVENTOS ---

    # Para Alunos
    if user.is_student():
        approved_attendances = AttendanceRequest.objects.filter(student=user, status='APR', notified=False)
        if approved_attendances.exists():
            count = approved_attendances.count()
            total_count += count
            notifications.append({
                'title': 'Presença Aprovada',
                'text': f'{count} presença(s) aprovada(s).',
                'url': 'aluno_presencas',
                'type': 'info'
            })

        new_graduations = Graduacao.objects.filter(aluno=user, notified=False)
        if new_graduations.exists():
            count = new_graduations.count()
            total_count += count
            notifications.append({
                'title': 'Nova Graduação',
                'text': 'Parabéns! Você tem uma nova graduação.',
                'url': 'aluno_graduacoes',
                'type': 'success'
            })

    # Para Professores e Admins
    if user.is_professor_or_admin():
        pending_attendances = AttendanceRequest.objects.filter(status='PEN')
        if pending_attendances.exists():
            count = pending_attendances.count()
            total_count += count
            notifications.append({
                'title': 'Solicitação de Presença',
                'text': f'{count} solicitação(ões) pendente(s).',
                'url': 'professor_presencas',
                'type': 'warning'
            })

        pending_users = User.objects.filter(status='PENDENTE')
        if pending_users.exists():
            count = pending_users.count()
            total_count += count
            notifications.append({
                'title': 'Novos Usuários',
                'text': f'{count} usuário(s) aguardando aprovação.',
                'url': 'professor_alunos',
                'type': 'warning'
            })

    # --- VERIFICAÇÃO DE PENDÊNCIAS CADASTRAIS (GRANULAR) ---
    
    # 1. DADOS DO PERFIL (Aplica-se a ALUNOS e PROFESSORES)
    # Lista de campos obrigatórios e seus labels amigáveis
    profile_fields = [
        ('first_name', 'Nome'),
        ('last_name', 'Sobrenome'),
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('birthday', 'Data de Nascimento'),
        ('photo', 'Foto de Perfil')
    ]

    for field_name, label in profile_fields:
        if not getattr(user, field_name):
            total_count += 1
            notifications.append({
                'title': 'Dados do Perfil',
                'text': f'O campo "{label}" é obrigatório.',
                'url': 'perfil_editar',
                'type': 'danger'
            })

    # 2. DADOS ESPECÍFICOS DE ALUNO (Graduação e Kimono)
    if user.is_student():
        # Graduação
        try:
            user.graduacoes.first() # Verifica se existe alguma graduação
        except ObjectDoesNotExist:
             # Se não existe objeto graduação, conta como pendência de Faixa e Grau
             # Nota: O modelo original tinha related_name='graduacoes', então user.graduacoes.exists() seria melhor
             pass
        
        if not user.graduacoes.exists():
            total_count += 1
            notifications.append({
                'title': 'Dados do Perfil',
                'text': 'Informe sua faixa e grau.',
                'url': 'perfil_editar',
                'type': 'danger'
            })

        # Meu Kimono
        kimono_fields = [
            ('height', 'a sua altura'),
            ('weight', 'o seu peso'),
            ('kimono_size', 'o tamanho do seu kimono'),
            ('belt_size', 'o tamanho da sua faixa')
        ]

        for field_name, label in kimono_fields:
            if not getattr(user, field_name):
                total_count += 1
                notifications.append({
                    'title': 'Meu Kimono',
                    'text': f'Informe {label}.',
                    'url': 'perfil',
                    'type': 'danger'
                })

    if notifications:
        return {
            'notifications': notifications, 
            'has_pending_tasks': True,
            'notification_count': total_count
        }
        
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
