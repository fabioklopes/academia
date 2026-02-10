from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from academia import views
from academia.forms import CustomPasswordResetForm


urlpatterns = [
    # Home/Index
    path('', views.dashboard, name='index'),

    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('solicitar-acesso/', views.solicitar_acesso, name='solicitar_acesso'),
    path('verificar-email-responsavel/', views.verificar_email_responsavel, name='verificar_email_responsavel'),
    path('switch-account/<int:user_id>/', views.switch_account, name='switch_account'),
    path('switch-account-back/', views.switch_account_back, name='switch_account_back'),
    
    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='academia/password_reset.html',
        form_class=CustomPasswordResetForm,
        email_template_name='academia/password_reset_email.html',
        subject_template_name='academia/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='academia/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='academia/password_reset_complete.html'), name='password_reset_complete'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Perfil
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.perfil_editar, name='perfil_editar'),
    path('perfil/photo/update/', views.perfil_photo_update, name='perfil_photo_update'), # New URL for photo update
    
    # Logs
    path('logs/', views.log_list, name='logs'),
    
    # Painel do Aluno
    path('aluno/marcar-presenca/', views.aluno_marcar_presenca, name='aluno_marcar_presenca'),
    path('aluno/get-attendance-details/', views.get_attendance_details, name='get_attendance_details'),
    path('aluno/cancelar-presenca/<int:request_id>/', views.aluno_cancelar_presenca, name='aluno_cancelar_presenca'),
    path('aluno/presencas/', views.aluno_presencas, name='aluno_presencas'),
    path('aluno/relatorios/', views.aluno_relatorios, name='aluno_relatorios'),
    path('aluno/graduacoes/', views.aluno_graduacoes, name='aluno_graduacoes'),
    path('aluno/pedidos/', views.aluno_pedidos, name='aluno_pedidos'),
    path('aluno/pedidos/novo/', views.aluno_pedido_novo, name='aluno_pedido_novo'),
    path('aluno/pedidos/<int:pedido_id>/cancelar/', views.aluno_pedido_cancelar, name='aluno_pedido_cancelar'),
    path('aluno/relatorios/presenca/', views.aluno_relatorio_presenca, name='aluno_relatorio_presenca'),
    path('aluno/relatorios/pedidos/', views.aluno_relatorio_pedidos, name='aluno_relatorio_pedidos'),
    
    # Painel do Professor - Turmas
    path('professor/turmas/', views.professor_turmas, name='professor_turmas'),
    path('professor/turmas/nova/', views.professor_turma_nova, name='professor_turma_nova'),
    path('professor/turmas/<int:turma_id>/editar/', views.professor_turma_editar, name='professor_turma_editar'),
    path('professor/turmas/<int:turma_id>/alunos/', views.professor_turma_alunos, name='professor_turma_alunos'),
    path('professor/turmas/<int:turma_id>/alunos/adicionar/', views.professor_turma_adicionar_aluno, name='professor_turma_adicionar_aluno'),
    path('professor/turmas/<int:turma_id>/alunos/<int:aluno_id>/remover/', views.professor_turma_remover_aluno, name='professor_turma_remover_aluno'),

    # Painel do Professor - Alunos
    path('professor/alunos/', views.professor_alunos, name='professor_alunos'),
    path('professor/promover-aluno/', views.promover_aluno, name='promover_aluno'),
    path('professor/aluno/<int:aluno_id>/desativar/', views.professor_aluno_desativar, name='professor_aluno_desativar'),
    path('professor/aluno/<int:aluno_id>/ativar/', views.professor_aluno_ativar, name='professor_aluno_ativar'),
    path('professor/aluno/<int:aluno_id>/excluir/', views.professor_aluno_excluir, name='professor_aluno_excluir'),
    path('professor/aluno/<int:aluno_id>/definir-tipo/', views.professor_aluno_definir_tipo, name='professor_aluno_definir_tipo'),
    path('professor/tamanhos-medidas/', views.tamanhos_medidas, name='tamanhos_medidas'),

    # Painel do Professor - Presenças
    path('professor/presencas/', views.professor_presencas, name='professor_presencas'),
    path('professor/presenca/<int:request_id>/aprovar/', views.professor_presenca_aprovar, name='professor_presenca_aprovar'),
    path('professor/presenca/<int:request_id>/rejeitar/', views.professor_presenca_rejeitar, name='professor_presenca_rejeitar'),

    # Painel do Professor - Graduacoes
    path('professor/graduacoes/', views.professor_graduacoes, name='professor_graduacoes'),
    path('professor/graduacao/<int:aluno_id>/editar/', views.professor_graduacao_editar, name='professor_graduacao_editar'),

    # Painel do Professor - Itens
    path('professor/itens/', views.professor_itens, name='professor_itens'),
    path('professor/itens/novo/', views.professor_item_novo, name='professor_item_novo'),
    path('professor/itens/<int:item_id>/editar/', views.professor_item_editar, name='professor_item_editar'),
    path('professor/itens/<int:item_id>/deletar/', views.professor_item_deletar, name='professor_item_deletar'),

    # Painel do Professor - Pedidos
    path('professor/pedidos/', views.professor_pedidos, name='professor_pedidos'),
    path('professor/pedido/<int:pedido_id>/aprovar/', views.professor_pedido_aprovar, name='professor_pedido_aprovar'),
    path('professor/pedido/<int:pedido_id>/rejeitar/', views.professor_pedido_rejeitar, name='professor_pedido_rejeitar'),
    path('professor/pedido/<int:pedido_id>/cancelar/', views.professor_pedido_cancelar, name='professor_pedido_cancelar'),
    path('professor/pedido/<int:pedido_id>/entregar/', views.professor_pedido_entregar, name='professor_pedido_entregar'),
    path('professor/pedido/<int:pedido_id>/finalizar/', views.professor_pedido_finalizar, name='professor_pedido_finalizar'),

    # Painel do Professor - Planos de Aula
    path('professor/planos-aula/', views.professor_planos_aula, name='professor_planos_aula'),
    path('professor/planos-aula/novo/', views.professor_plano_aula_novo, name='professor_plano_aula_novo'),
    path('professor/planos-aula/<int:plano_id>/editar/', views.professor_plano_aula_editar, name='professor_plano_aula_editar'),

    # Painel do Professor - Rankings
    path('professor/rankings/', views.professor_rankings, name='professor_rankings'),
    path('professor/rankings/novo/', views.professor_ranking_novo, name='professor_ranking_novo'),

    # Painel do Professor - Metas
    path('professor/metas/', views.professor_metas, name='professor_metas'),
    path('professor/metas/nova/', views.professor_meta_nova, name='professor_meta_nova'),
    path('professor/metas/<int:meta_id>/editar/', views.professor_meta_editar, name='professor_meta_editar'),
    path('professor/metas/<int:meta_id>/deletar/', views.professor_meta_deletar, name='professor_meta_deletar'),

    # Painel do Professor - Relatórios
    path('professor/relatorios/', views.professor_relatorios, name='professor_relatorios'),
    path('professor/relatorios/pedidos/', views.relatorio_pedidos, name='relatorio_pedidos'),
    path('professor/relatorios/presenca/', views.relatorio_presenca, name='professor_relatorio_presenca'),
]

# Página padrão para erros no aplicativo
handler400 = 'academia.views.error_400'
handler403 = 'academia.views.error_403'
handler404 = 'academia.views.error_404'
handler413 = 'academia.views.error_413'
handler500 = 'academia.views.error_500'
