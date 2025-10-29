import datetime
import time
import os
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.utils import timezone
from .models import User, Class, AttendanceRequest

# --- VIEWS GERAIS ---

def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        access_group_form = request.POST.get('access_group')

        try:
            user = User.objects.get(email=email, status=1)

            if user.access_group != access_group_form:
                return render(request, 'login.html', {'error': 'Tipo de acesso incorreto para este usuário.'})

            # Verifica a senha usando SHA256
            hashed_password_form = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if hashed_password_form == user.keypass:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, user)
                
                if user.access_group == 'PRO':
                    return redirect('teacher_dashboard')
                elif user.access_group == 'STU':
                    return redirect('my_attendence_requests')
                else: # ADM
                    return redirect('index')
            else:
                return render(request, 'login.html', {'error': 'Credenciais inválidas.'})

        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'Usuário não encontrado ou inativo.'})

    return render(request, 'login.html')

def logout_view(request):
    auth_logout(request)
    return redirect('index')

# --- FUNÇÕES DE VERIFICAÇÃO DE GRUPO ---

def is_student(user):
    return user.is_authenticated and user.access_group == 'STU'

def is_teacher(user):
    return user.is_authenticated and user.access_group == 'PRO'

# --- VIEWS DE ALUNOS (CRUD) ---

@login_required
@user_passes_test(is_teacher)
def list_students(request):
    students = User.objects.filter(access_group='STU', status=1).order_by('first_name')
    context = {
        'students': students
    }
    return render(request, 'alunos.html', context)

def new_student(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        identification = request.POST.get('identification')
        birthday = request.POST.get('birthday')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        current_belt = request.POST.get('current_belt')
        current_degree = request.POST.get('current_degree')
        start_date = request.POST.get('start_date')
        image_profile = request.FILES.get('image_profile')

        if image_profile and first_name:
            timestamp = int(time.time())
            safe_first_name = "".join(c for c in first_name if c.isalnum()).lower()
            new_filename = f"{safe_first_name}-{timestamp}.jpg"
            image_profile.name = new_filename

        if not start_date:
            start_date = None

        # Criptografa a senha com SHA256
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        User.objects.create(
            first_name=first_name,
            last_name=last_name,
            identification=identification,
            birthday=birthday,
            email=email,
            keypass=hashed_password,
            access_group='STU',
            phone=phone,
            start_date=start_date,
            current_belt=current_belt,
            current_degree=current_degree,
            image_profile=image_profile
        )
        return redirect('login')

    return render(request, 'new_student.html')

@login_required
@user_passes_test(is_teacher)
def edit_student(request, user_id):
    student = get_object_or_404(User, pk=user_id, access_group='STU', status=1)

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        student.first_name = first_name
        student.last_name = request.POST.get('last_name')
        student.identification = request.POST.get('identification')
        student.birthday = request.POST.get('birthday')
        student.email = request.POST.get('email')
        student.phone = request.POST.get('phone')
        student.current_belt = request.POST.get('current_belt')
        student.current_degree = request.POST.get('current_degree')
        start_date = request.POST.get('start_date')

        if not start_date:
            student.start_date = None
        else:
            student.start_date = start_date
        
        if 'image_profile' in request.FILES:
            image_profile = request.FILES['image_profile']
            if image_profile and first_name:
                timestamp = int(time.time())
                safe_first_name = "".join(c for c in first_name if c.isalnum()).lower()
                new_filename = f"{safe_first_name}-{timestamp}.jpg"
                image_profile.name = new_filename
            student.image_profile = image_profile

        student.save()
        return redirect('list_students')

    context = {
        'student': student,
        'belts': User.BELTS,
        'degrees': User.DEGREES
    }
    return render(request, 'edit_student.html', context)

@login_required
@user_passes_test(is_teacher)
def delete_student(request, user_id):
    student = get_object_or_404(User, pk=user_id, access_group='STU')
    if request.method == 'POST':
        student.status = 0
        student.save()
        return redirect('list_students')
    context = {'student': student}
    return render(request, 'delete_student.html', context)

# --- VIEWS DE SOLICITAÇÃO DE PRESENÇA (ALUNO) ---

@login_required
@user_passes_test(is_student)
def request_attendance(request):
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        dates = request.POST.getlist('dates')
        reason = request.POST.get('reason')
        class_obj = get_object_or_404(Class, pk=class_id)

        for date_str in dates:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            AttendanceRequest.objects.create(
                student=request.user,
                class_obj=class_obj,
                attendence_date=date,
                reason=reason
            )
        return redirect('my_attendence_requests')

    classes = Class.objects.filter(status=True)
    context = {
        'classes': classes
    }
    return render(request, 'request_attendence.html', context)

@login_required
@user_passes_test(is_student)
def my_attendance_requests(request):
    requests = AttendanceRequest.objects.filter(student=request.user)
    context = {
        'requests': requests
    }
    return render(request, 'my_attendance_requests.html', context)

@login_required
@user_passes_test(is_student)
def cancel_attendance_request(request, request_id):
    att_request = get_object_or_404(AttendanceRequest, pk=request_id, student=request.user, status='PEN')
    att_request.status = 'CAN'
    att_request.save()
    return redirect('my_attendence_requests')

# --- VIEWS DE GERENCIAMENTO DE PRESENÇA (PROFESSOR) ---

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    pending_requests_count = AttendanceRequest.objects.filter(status='PEN').count()
    active_students_count = User.objects.filter(access_group='STU', status=1).count()
    context = {
        'pending_requests_count': pending_requests_count,
        'active_students_count': active_students_count,
    }
    return render(request, 'teacher_dashboard.html', context)

@login_required
@user_passes_test(is_teacher)
def list_attendance_requests(request):
    pending_requests = AttendanceRequest.objects.filter(status='PEN')
    processed_requests = AttendanceRequest.objects.filter(processed_by=request.user).exclude(status='PEN')
    context = {
        'pending_requests': pending_requests,
        'processed_requests': processed_requests
    }
    return render(request, 'list_attendance_requests.html', context)

@login_required
@user_passes_test(is_teacher)
def process_attendance_request(request, request_id):
    att_request = get_object_or_404(AttendanceRequest, pk=request_id, status='PEN')

    if request.method == 'POST':
        action = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason')

        if action == 'approve':
            att_request.status = 'APR'
        elif action == 'reject':
            att_request.status = 'REJ'
            att_request.rejection_reason = rejection_reason
        
        att_request.processed_by = request.user
        att_request.processed_at = timezone.now()
        att_request.save()
        return redirect('list_attendance_requests')

    context = {
        'request': att_request
    }
    return render(request, 'process_attendance_request.html', context)
