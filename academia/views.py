import datetime

from django.contrib.auth import logout, login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import User, Class, AttendenceRequest


def index(request):
    students = User.objects.all().filter(access_group='STU', status=1)
    professors = User.objects.all().filter(access_group='PRO', status=1)

    context = {
        'students': students,
        'professors': professors,
    }

    return render(request, 'index.html', context)

def login_view(request):
    login(request)
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('index')


# --- FUNÇÕES DE VERIFICAÇÃO DE GRUPO ---
def is_student(user):
    return user.is_authenticated and user.access_group == 'STU'

def is_teacher(user):
    return user.is_authenticated and user.access_group == 'PRO'

# --- VIEWS DE ALUNOS (CRUD) ---

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
        phone = request.POST.get('phone')
        current_belt = request.POST.get('current_belt')
        current_degree = request.POST.get('current_degree')
        start_date = request.POST.get('start_date')
        image_profile = request.FILES.get('image_profile')

        if not start_date:
            start_date = None

        new_user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            identification=identification,
            birthday=birthday,
            email=email,
            keypass=make_password(identification),
            access_group='STU',
            phone=phone,
            start_date=start_date,
            current_belt=current_belt,
            current_degree=current_degree,
            image_profile=image_profile
        )
        return redirect('list_students')

    return render(request, 'new_student.html')

def edit_student(request, user_id):
    student = get_object_or_404(User, pk=user_id, access_group='STU', status=1)

    if request.method == 'POST':
        student.first_name = request.POST.get('first_name')
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
            student.image_profile = request.FILES.get('image_profile')

        student.save()
        return redirect('list_students')

    context = {
        'student': student,
        'belts': User.BELTS,
        'degrees': User.DEGREES
    }
    return render(request, 'edit_student.html', context)

def delete_student(request, user_id):
    student = get_object_or_404(User, pk=user_id, access_group='STU')

    if request.method == 'POST':
        student.status = 0
        student.save()
        return redirect('list_students')

    context = {
        'student': student
    }
    return render(request, 'delete_student.html', context)

# --- VIEWS DE SOLICITAÇÃO DE PRESENÇA (ALUNO) ---

@login_required
@user_passes_test(is_student)
def request_attendence(request):
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        dates = request.POST.getlist('dates')
        reason = request.POST.get('reason')
        class_obj = get_object_or_404(Class, pk=class_id)

        for date_str in dates:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            AttendenceRequest.objects.create(
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
def my_attendence_requests(request):
    requests = AttendenceRequest.objects.filter(student=request.user)
    context = {
        'requests': requests
    }
    return render(request, 'my_attendence_requests.html', context)

@login_required
@user_passes_test(is_student)
def cancel_attendence_request(request, request_id):
    att_request = get_object_or_404(AttendenceRequest, pk=request_id, student=request.user, status='PEN')
    att_request.status = 'CAN'
    att_request.save()
    return redirect('my_attendence_requests')

# --- VIEWS DE GERENCIAMENTO DE PRESENÇA (PROFESSOR) ---

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    pending_requests_count = AttendenceRequest.objects.filter(status='PEN').count()
    active_students_count = User.objects.filter(access_group='STU', status=1).count()
    context = {
        'pending_requests_count': pending_requests_count,
        'active_students_count': active_students_count,
    }
    return render(request, 'teacher_dashboard.html', context)

@login_required
@user_passes_test(is_teacher)
def list_attendence_requests(request):
    pending_requests = AttendenceRequest.objects.filter(status='PEN')
    processed_requests = AttendenceRequest.objects.filter(processed_by=request.user).exclude(status='PEN')
    context = {
        'pending_requests': pending_requests,
        'processed_requests': processed_requests
    }
    return render(request, 'list_attendence_requests.html', context)

@login_required
@user_passes_test(is_teacher)
def process_attendence_request(request, request_id):
    att_request = get_object_or_404(AttendenceRequest, pk=request_id, status='PEN')

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
        return redirect('list_attendence_requests')

    context = {
        'request': att_request
    }
    return render(request, 'process_attendence_request.html', context)
