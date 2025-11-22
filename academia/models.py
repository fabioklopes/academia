from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import time

def photo_upload_to(instance, filename):
    timestamp = str(int(time.time()))
    return f'photos/{instance.pk}_{timestamp}.png' if instance.pk else f'photos/temp_{timestamp}.png'

class User(AbstractUser):
    GROUP_ROLE_CHOICES = [('STD', 'Aluno'), ('PRO', 'Professor'), ('ADM', 'Administrador')]
    KIMONO_SIZE_CHOICES = [('A0', 'A0'), ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4')]
    BELT_SIZE_CHOICES = [('A0', 'A0'), ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4')]

    birthday = models.DateField('Data de Nascimento', null=True, blank=True)
    group_role = models.CharField('Perfil', max_length=3, choices=GROUP_ROLE_CHOICES, default='STD')
    active = models.BooleanField('Ativo', default=True)
    photo = models.ImageField('Foto', upload_to=photo_upload_to, null=True, blank=True)
    height = models.IntegerField('Altura (cm)', null=True, blank=True)
    weight = models.IntegerField('Peso (kg)', null=True, blank=True)
    kimono_size = models.CharField('Tamanho do Kimono', max_length=2, choices=KIMONO_SIZE_CHOICES, null=True, blank=True)
    belt_size = models.CharField('Tamanho da Faixa', max_length=2, choices=BELT_SIZE_CHOICES, null=True, blank=True)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Usuário', 'Usuários'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return self.get_full_name()
    
    def is_student(self): return self.group_role == 'STD'
    def is_professor(self): return self.group_role == 'PRO'
    def is_admin(self): return self.group_role == 'ADM'
    def is_professor_or_admin(self): return self.group_role in ['PRO', 'ADM']

class Turma(models.Model):
    nome = models.CharField('Nome da Turma', max_length=100)
    descricao = models.TextField('Descrição', blank=True)
    professor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'group_role__in': ['PRO', 'ADM']}, related_name='turmas_professor')
    alunos = models.ManyToManyField(User, through='TurmaAluno', related_name='turmas', limit_choices_to={'group_role': 'STD'})
    ativa = models.BooleanField('Ativa', default=True)
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Turma', 'Turmas'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.professor.first_name}"

class TurmaAluno(models.Model):
    STATUS_CHOICES = [('PEND', 'Pendente'), ('APRO', 'Aprovado'), ('REJE', 'Rejeitado')]
    
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    aluno = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField('Status', max_length=4, choices=STATUS_CHOICES, default='PEND')
    data_solicitacao = models.DateTimeField('Data de Solicitação', auto_now_add=True)
    data_aprovacao = models.DateTimeField('Data de Aprovação', null=True, blank=True)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Solicitação de Turma', 'Solicitações de Turma'
        unique_together = ['turma', 'aluno']
    
    def __str__(self):
        return f"{self.aluno} - {self.turma}"

class AttendanceRequest(models.Model):
    STATUS_CHOICES = [('PEN', 'Pendente'), ('APR', 'Aprovado'), ('REJ', 'Rejeitado'), ('CAN', 'Cancelado')]

    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'group_role': 'STD'}, related_name='attendance_requests')
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='attendance_requests')
    attendance_date = models.DateField('Data da Presença')
    reason = models.TextField('Motivo da Solicitação')
    status = models.CharField('Status', max_length=3, choices=STATUS_CHOICES, default='PEN')
    rejection_reason = models.TextField('Motivo da Rejeição', blank=True)
    processed_at = models.DateTimeField('Data de Processamento', null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'group_role__in': ['PRO', 'ADM']}, related_name='processed_requests')
    notified = models.BooleanField(default=False)

    class Meta:
        verbose_name, verbose_name_plural = 'Solicitação de Presença', 'Solicitações de Presença'
        ordering = ['-attendance_date']
        unique_together = ['student', 'turma', 'attendance_date']

    def __str__(self):
        return f"{self.student} - {self.attendance_date} - {self.get_status_display()}"

class Graduacao(models.Model):
    FAIXA_CHOICES = [
        ('BRANCA', 'Branca'), ('CINZA_BRANCA', 'Cinza e Branca'), ('CINZA', 'Cinza'), ('CINZA_PRETA', 'Cinza e Preta'),
        ('AMARELA_BRANCA', 'Amarela e Branca'), ('AMARELA', 'Amarela'), ('AMARELA_PRETA', 'Amarela e Preta'),
        ('LARANJA_BRANCA', 'Laranja e Branca'), ('LARANJA', 'Laranja'), ('LARANJA_PRETA', 'Laranja e Preta'),
        ('VERDE_BRANCA', 'Verde e Branca'), ('VERDE', 'Verde'), ('VERDE_PRETA', 'Verde e Preta'),
        ('AZUL', 'Azul'), ('ROXA', 'Roxa'), ('MARROM', 'Marrom'), ('PRETA', 'Preta'),
    ]
    
    aluno = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'group_role': 'STD'}, related_name='graduacao')
    faixa = models.CharField('Faixa', max_length=15, choices=FAIXA_CHOICES, default='BRANCA')
    grau = models.IntegerField('Grau', validators=[MinValueValidator(0), MaxValueValidator(6)], default=0)
    data_graduacao = models.DateField('Data da Graduação', null=True, blank=True)
    notified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Graduação', 'Graduações'
    
    def __str__(self):
        return f"{self.aluno} - {self.get_faixa_display()} - {self.grau}º grau"

class PlanoAula(models.Model):
    titulo = models.CharField('Título', max_length=200)
    descricao = models.TextField('Descrição')
    professor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'group_role__in': ['PRO', 'ADM']}, related_name='planos_aula')
    data_inicio = models.DateField('Data de Início')
    data_fim = models.DateField('Data de Término', null=True, blank=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='planos_aula', null=True, blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Plano de Aula', 'Plano de Aulas'
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f"{self.titulo} - {self.professor.first_name}"

class ItemPlanoAula(models.Model):
    plano = models.ForeignKey(PlanoAula, on_delete=models.CASCADE, related_name='itens')
    assunto = models.CharField('Assunto', max_length=200)
    data_aula = models.DateField('Data da Aula')
    ordem = models.IntegerField('Ordem', default=1)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Item do Plano de Aula', 'Itens do Plano de Aula'
        ordering = ['plano', 'data_aula', 'ordem']
    
    def __str__(self):
        return f"{self.plano} - {self.assunto}"

class Ranking(models.Model):
    TIPO_CHOICES = [('FALTAS', 'Menos Faltas'), ('CAMPEONATO', 'Mini-Campeonato'), ('ALUNO_DESTAQUE', 'Aluno Destaque')]
    
    titulo = models.CharField('Título', max_length=200)
    tipo = models.CharField('Tipo', max_length=15, choices=TIPO_CHOICES)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='rankings', null=True, blank=True)
    data_inicio = models.DateField('Data de Início')
    data_fim = models.DateField('Data de Término', null=True, blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Ranking', 'Rankings'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.titulo} - {self.turma.nome if self.turma else 'Todas as Turmas'} - {self.get_tipo_display()}"

class PosicaoRanking(models.Model):
    ranking = models.ForeignKey(Ranking, on_delete=models.CASCADE, related_name='posicoes')
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'group_role': 'STD'}, related_name='posicoes_ranking')
    posicao = models.IntegerField('Posição')
    pontuacao = models.FloatField('Pontuação', default=0)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Posição no Ranking', 'Posições no Ranking'
        ordering = ['ranking', 'posicao']
        unique_together = ['ranking', 'aluno']
    
    def __str__(self):
        return f"{self.ranking} - {self.aluno} - {self.posicao}º lugar"

class Item(models.Model):
    TIPO_CHOICES = [('KIMONO', 'Kimono'), ('FAIXA', 'Faixa'), ('RASHGUARD', 'Rashguard'), ('TAXA', 'Taxa')]
    nome = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantidade = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.nome

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('PEND', 'Pendente'), ('APRO', 'Aprovado'), ('CANC', 'Cancelado'),
        ('REJE', 'Rejeitado'), ('ENTR', 'Aguardando entrega'), ('FINA', 'Finalizado')
    ]
    
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'group_role': 'STD'}, related_name='pedidos')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='pedidos')
    quantidade = models.IntegerField(default=1)
    status = models.CharField('Status', max_length=4, choices=STATUS_CHOICES, default='PEND')
    data_solicitacao = models.DateTimeField('Data de Solicitação', auto_now_add=True)
    data_aprovacao = models.DateTimeField('Data de Aprovação', null=True, blank=True)
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'group_role__in': ['PRO', 'ADM']}, related_name='pedidos_aprovados')
    rejection_reason = models.TextField('Motivo da Rejeição', blank=True, null=True)
    cancellation_reason = models.TextField('Motivo do Cancelamento', blank=True, null=True)
    final_value = models.DecimalField('Valor Final', max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Pedido', 'Pedidos'
        ordering = ['-data_solicitacao']
    
    def __str__(self):
        return f"{self.aluno} - {self.item.nome} - {self.get_status_display()}"
