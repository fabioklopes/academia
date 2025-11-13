from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Turma, TurmaAluno, Presenca, Graduacao,
    PlanoAula, ItemPlanoAula, Ranking, PosicaoRanking, Pedido
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'group_role', 'active']
    list_filter = ['group_role', 'active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('birthday', 'group_role', 'active', 'photo')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações Adicionais', {
            'fields': ('birthday', 'group_role', 'active', 'photo')
        }),
    )


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'professor', 'ativa', 'data_criacao']
    list_filter = ['ativa', 'data_criacao']
    search_fields = ['nome', 'professor__first_name', 'professor__last_name']


@admin.register(TurmaAluno)
class TurmaAlunoAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'turma', 'status', 'data_solicitacao']
    list_filter = ['status', 'data_solicitacao']
    search_fields = ['aluno__first_name', 'aluno__last_name', 'turma__nome']


@admin.register(Presenca)
class PresencaAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'turma', 'data_presenca', 'status', 'data_solicitacao']
    list_filter = ['status', 'data_presenca', 'turma']
    search_fields = ['aluno__first_name', 'aluno__last_name']


@admin.register(Graduacao)
class GraduacaoAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'faixa', 'grau', 'data_graduacao']
    list_filter = ['faixa', 'grau']
    search_fields = ['aluno__first_name', 'aluno__last_name']


@admin.register(PlanoAula)
class PlanoAulaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'professor', 'turma', 'data_inicio', 'ativo']
    list_filter = ['ativo', 'data_inicio', 'turma']
    search_fields = ['titulo', 'professor__first_name', 'professor__last_name']


@admin.register(ItemPlanoAula)
class ItemPlanoAulaAdmin(admin.ModelAdmin):
    list_display = ['plano', 'assunto', 'data_aula', 'ordem']
    list_filter = ['data_aula', 'plano']
    search_fields = ['assunto', 'plano__titulo']


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'turma', 'data_inicio', 'data_fim', 'ativo']
    list_filter = ['tipo', 'ativo', 'data_inicio']
    search_fields = ['titulo', 'turma__nome']


@admin.register(PosicaoRanking)
class PosicaoRankingAdmin(admin.ModelAdmin):
    list_display = ['ranking', 'aluno', 'posicao', 'pontuacao']
    list_filter = ['ranking', 'posicao']
    search_fields = ['aluno__first_name', 'aluno__last_name', 'ranking__titulo']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'tipo', 'status', 'data_solicitacao']
    list_filter = ['tipo', 'status', 'data_solicitacao']
    search_fields = ['aluno__first_name', 'aluno__last_name']

