from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    # API de Alunos
    path('api/alunos/', views.list_students, name='list_students'),
    path('api/alunos/novoaluno/', views.new_student, name='new_student'),
    path('api/alunos/editaraluno/<int:user_id>/', views.edit_student, name='edit_student'),
    path('api/alunos/removeraluno/<int:user_id>/', views.delete_student, name='delete_student'),
]
