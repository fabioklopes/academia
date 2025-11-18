from .models import User, AttendanceRequest, Pedido, Graduacao

def pending_tasks_processor(request):
    if not request.user.is_authenticated:
        return {}

    notifications = []
    has_pending_tasks = False

    # Student notifications
    if request.user.is_student():
        approved_attendance_count = AttendanceRequest.objects.filter(student=request.user, status='APR', notified=False).count()
        new_graduations_count = Graduacao.objects.filter(aluno=request.user, notified=False).count()

        if approved_attendance_count > 0:
            notifications.append({
                'text': f"{approved_attendance_count} solicitação(ões) de presença aprovada(s)",
                'url': 'aluno_presencas'
            })
        if new_graduations_count > 0:
            notifications.append({
                'text': f"{new_graduations_count} nova(s) graduação(ões)",
                'url': 'aluno_graduacoes'
            })

    # Professor/Admin notifications
    elif request.user.is_professor_or_admin():
        pending_students_count = User.objects.filter(is_active=False, group_role='STD').count()
        
        if request.user.is_admin():
            pending_attendance_count = AttendanceRequest.objects.filter(status='PEN').count()
            pending_pedidos_count = Pedido.objects.filter(status='PEND').count()
        else: # Professor
            pending_attendance_count = AttendanceRequest.objects.filter(turma__professor=request.user, status='PEN').count()
            pending_pedidos_count = Pedido.objects.filter(aluno__turmas__professor=request.user, status='PEND').distinct().count()

        if pending_students_count > 0:
            notifications.append({
                'text': f"{pending_students_count} novo(s) aluno(s) aguardando aprovação",
                'url': 'professor_alunos'
            })
        if pending_attendance_count > 0:
            notifications.append({
                'text': f"{pending_attendance_count} nova(s) solicitação(ões) de presença",
                'url': 'professor_presencas'
            })
        if pending_pedidos_count > 0:
            notifications.append({
                'text': f"{pending_pedidos_count} novo(s) pedido(s)",
                'url': 'professor_pedidos'
            })

    if notifications:
        has_pending_tasks = True

    return {
        'notifications': notifications,
        'has_pending_tasks': has_pending_tasks,
    }
