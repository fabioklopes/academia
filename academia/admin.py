from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Turma, TurmaAluno,
    PlanoAula, ItemPlanoAula, Ranking, PosicaoRanking, Pedido, Item, Log
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'group_role', 'is_active']
    list_filter = ['group_role', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {
            'fields': ('birthday', 'group_role', 'photo')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações Adicionais', {
            'fields': ('birthday', 'group_role', 'photo')
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


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'valor', 'quantidade']
    list_filter = ['tipo']
    search_fields = ['nome']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['aluno', 'item', 'quantidade', 'status', 'data_solicitacao']
    list_filter = ['status', 'data_solicitacao', 'item__tipo']
    search_fields = ['aluno__first_name', 'aluno__last_name', 'item__nome']


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('timestamp', 'user')
    search_fields = ('user__username', 'action')
    readonly_fields = ('user', 'action', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
