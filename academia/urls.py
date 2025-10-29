from django.urls import path
from . import views

urlpatterns = [
    # URLs Gerais
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),


    # URLs de Alunos (CRUD)
    path('api/alunos/', views.list_students, name='list_students'),
    path('api/alunos/novoaluno/', views.new_student, name='new_student'),
    path('api/alunos/editaraluno/<int:user_id>/', views.edit_student, name='edit_student'),
    path('api/alunos/removeraluno/<int:user_id>/', views.delete_student, name='delete_student'),


    # URLs de Solicitação de Presença (Aluno)
    path('presenca/solicitar/', views.request_attendence, name='request_attendence'),
    path('presenca/minhas-solicitacoes/', views.my_attendence_requests, name='my_attendence_requests'),
    path('presenca/cancelar/<int:request_id>/', views.cancel_attendence_request, name='cancel_attendence_request'),


    # URLs de Gerenciamento de Presença (Professor)
    path('professor/painel/', views.teacher_dashboard, name='teacher_dashboard'),
    path('presenca/lista-solicitacoes/', views.list_attendence_requests, name='list_attendence_requests'),
    path('presenca/processar/<int:request_id>/', views.process_attendence_request, name='process_attendence_request'),
]
