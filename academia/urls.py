"""
    Developed by: Fábio Klevinskas Lopes
    Version: 3.0 (30/10/2025)
"""
from django.contrib.auth.decorators import login_required
from django.urls import path
from academia import views

urlpatterns = [
    # URLs Gerais
    path('', views.index, name='index'),
    path('api/login/', views.login_view, name='login'),
    path('api/logout/', views.logout_view, name='logout'),


    # ---------------------------------------------
    # URLs de Professor
    path('api/professor/painel/', views.teacher_dashboard, name='teacher_dashboard'),
    path('api/presenca/lista-solicitacoes/', views.list_attendance_requests, name='list_attendance_requests'),
    path('api/presenca/processar/<int:request_id>/', views.process_attendance_request, name='process_attendance_request'),




    # ---------------------------------------------
    # URLs de Alunos (CRUD)
    path('api/alunos/', views.list_students, name='list_students'),
    path('api/alunos/novoaluno/', views.new_student, name='new_student'),
    path('api/alunos/editaraluno/<int:user_id>/', views.edit_student, name='edit_student'),
    path('api/alunos/removeraluno/<int:user_id>/', views.delete_student, name='delete_student'),




    # ---------------------------------------------
    # URLs de Solicitação de Presença (Aluno)
    path('api/presenca/solicitar/', views.request_attendance, name='request_attendance'),
    path('api/presenca/minhas-solicitacoes/', views.my_attendance_requests, name='my_attendance_requests'),
    path('api/presenca/cancelar/<int:request_id>/', views.cancel_attendance_request, name='cancel_attendance_request'),


]
