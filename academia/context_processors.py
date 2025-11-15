from .models import User, AttendanceRequest, Pedido

def pending_tasks_processor(request):
    if not request.user.is_authenticated:
        return {}

    # For Students: Only show notifications from Professor/Admin
    if request.user.is_student():
        # For now, students don't have specific pending tasks displayed in the toast
        # This can be extended later if needed for student-specific notifications
        return {
            'has_pending_tasks': False,
        }

    # For Professors and Admins: Show administrative pending tasks
    elif request.user.is_professor() or request.user.is_admin():
        pending_students_count = 0
        pending_attendance_count = 0
        pending_pedidos_count = 0

        if request.user.is_admin:
            pending_students_count = User.objects.filter(is_active=False, group_role='STD').count()
            pending_attendance_count = AttendanceRequest.objects.filter(status='PEN').count()
            pending_pedidos_count = Pedido.objects.filter(status='PEND').count()
        elif request.user.is_professor:
            pending_students_count = User.objects.filter(is_active=False, group_role='STD').count()
            pending_attendance_count = AttendanceRequest.objects.filter(turma__professor=request.user, status='PEN').count()
            pending_pedidos_count = Pedido.objects.filter(aluno__turmas__professor=request.user, status='PEND').distinct().count()

        total_pending = pending_students_count + pending_attendance_count + pending_pedidos_count
        has_pending_tasks = total_pending > 0

        return {
            'has_pending_tasks': has_pending_tasks,
            'pending_students_count': pending_students_count,
            'pending_attendance_count': pending_attendance_count,
            'pending_pedidos_count': pending_pedidos_count,
        }
    
    return {}
