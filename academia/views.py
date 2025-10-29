import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from .models import User

def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

def logout(request):
    return render(request, 'logout.html')

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

        new_user = User(
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
        new_user.save()
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
