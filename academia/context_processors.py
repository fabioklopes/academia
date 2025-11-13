from .models import User, AttendanceRequest, Pedido, Graduacao

def pending_tasks_processor(request):
    if not request.user.is_authenticated:
        return {}

    # For Students: Only show notifications from Professor/Admin
    if request.user.is_student():
        # Example: Check for newly approved attendance requests or graduations
        # For now, let's assume 'notified' field in Graduacao means it's a new notification
        # You might need to define what constitutes a "notification from professor/admin"
        # For this example, let's say approved attendance requests and new graduations
        
        # Count approved attendance requests that haven't been seen by the student
        # (This would require an additional field in AttendanceRequest like 'student_notified')
        # For now, we'll just count approved ones as a placeholder
        approved_attendance_count = AttendanceRequest.objects.filter(
            student=request.user, 
            status='APR',
            # student_notified=False # This field would need to be added to the model
        ).count()

        # Count new graduations that haven't been seen by the student
        new_graduations_count = Graduacao.objects.filter(
            aluno=request.user, 
            notified=False
        ).count()

        total_student_notifications = approved_attendance_count + new_graduations_count
        
        return {
            'has_pending_tasks': total_student_notifications > 0,
            'student_notifications_count': total_student_notifications,
            'approved_attendance_count': approved_attendance_count,
            'new_graduations_count': new_graduations_count,
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
