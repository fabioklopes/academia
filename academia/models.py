from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import time
import os


def photo_upload_to(instance, filename):
    """Generate filename for profile photos in format: id_timestamp.png"""
    timestamp = str(int(time.time()))
    # Ensure the instance has an ID before trying to use it
    if instance.pk:
        return f'photos/{instance.pk}_{timestamp}.png'
    else:
        # Handle cases where the instance might not have a primary key yet (e.g., during creation)
        # This might happen if the photo is uploaded before the user object is saved.
        # For now, we'll use a generic name or handle it as needed.
        # A more robust solution might involve saving the user first, then uploading the photo.
        return f'photos/temp_{timestamp}.png'


class User(AbstractUser):
    """Modelo customizado de usuário"""
    GROUP_ROLE_CHOICES = [
        ('STD', 'Aluno'),
        ('PRO', 'Professor'),
        ('ADM', 'Administrador'),
    ]

    birthday = models.DateField('Data de Nascimento', null=True, blank=True)
    group_role = models.CharField(
        'Perfil',
        max_length=3,
        choices=GROUP_ROLE_CHOICES,
        default='STD'
    )
    active = models.BooleanField('Ativo', default=True)  # pyright: ignore[reportArgumentType]
    photo = models.ImageField(
        'Foto',
        upload_to=photo_upload_to,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_student(self):
        return self.group_role == 'STD'
    
    def is_professor(self):
        return self.group_role == 'PRO'
    
    def is_admin(self):
        return self.group_role == 'ADM'
    
    def is_professor_or_admin(self):
        return self.group_role in ['PRO', 'ADM']


class Turma(models.Model):
    """Modelo para turmas da academia"""
    nome = models.CharField('Nome da Turma', max_length=100)
    descricao = models.TextField('Descrição', blank=True)
    professor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'group_role__in': ['PRO', 'ADM']},
        related_name='turmas_professor'
    )
    alunos = models.ManyToManyField(
        User,
        through='TurmaAluno',
        related_name='turmas',
        limit_choices_to={'group_role': 'STD'}
    )
    ativa = models.BooleanField('Ativa', default=True)  # pyright: ignore[reportArgumentType]
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.professor.first_name} {self.professor.last_name}"


class TurmaAluno(models.Model):
    """Modelo intermediário para relacionamento entre Turma e Aluno"""
    STATUS_CHOICES = [
        ('PEND', 'Pendente'),
        ('APRO', 'Aprovado'),
        ('REJE', 'Rejeitado'),
    ]
    
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    aluno = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        'Status',
        max_length=4,
        choices=STATUS_CHOICES,
        default='PEND'
    )
    data_solicitacao = models.DateTimeField('Data de Solicitação', auto_now_add=True)
    data_aprovacao = models.DateTimeField('Data de Aprovação', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Solicitação de Turma'
        verbose_name_plural = 'Solicitações de Turma'
        unique_together = ['turma', 'aluno']
    
    def __str__(self):
        return f"{self.aluno} - {self.turma}"


class AttendanceRequest(models.Model):
    """Modelo para solicitação de presença"""
    STATUS_CHOICES = [
        ('PEN', 'Pendente'),
        ('APR', 'Aprovado'),
        ('REJ', 'Rejeitado'),
        ('CAN', 'Cancelado'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'group_role': 'STD'},
        related_name='attendance_requests'
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='attendance_requests'
    )
    attendance_date = models.DateField('Data da Presença')
    reason = models.TextField('Motivo da Solicitação')
    status = models.CharField(
        'Status',
        max_length=3,
        choices=STATUS_CHOICES,
        default='PEN'
    )
    rejection_reason = models.TextField('Motivo da Rejeição', blank=True)
    processed_at = models.DateTimeField('Data de Processamento', null=True, blank=True)
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'group_role__in': ['PRO', 'ADM']},
        related_name='processed_requests'
    )

    class Meta:
        verbose_name = 'Solicitação de Presença'
        verbose_name_plural = 'Solicitações de Presença'
        ordering = ['-attendance_date']
        unique_together = ['student', 'turma', 'attendance_date']

    def __str__(self):
        return f"{self.student} - {self.attendance_date} - {self.get_status_display()}"


class Presenca(models.Model):
    """Modelo para controle de presenças"""
    STATUS_CHOICES = [
        ('PEND', 'Pendente'),
        ('APRO', 'Aprovado'),
        ('REJE', 'Rejeitado'),
    ]
    
    aluno = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'group_role': 'STD'},
        related_name='presencas'
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='presencas'
    )
    data_presenca = models.DateField('Data da Presença')
    status = models.CharField(
        'Status',
        max_length=4,
        choices=STATUS_CHOICES,
        default='PEND'
    )
    motivo_rejeicao = models.TextField('Motivo da Rejeição', blank=True)
    data_solicitacao = models.DateTimeField('Data de Solicitação', auto_now_add=True)
    data_aprovacao = models.DateTimeField('Data de Aprovação', null=True, blank=True)
    aprovado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'group_role__in': ['PRO', 'ADM']},
        related_name='presencas_aprovadas'
    )
    
    class Meta:
        verbose_name = 'Presença'
        verbose_name_plural = 'Presenças'
        ordering = ['-data_presenca']
        unique_together = ['aluno', 'turma', 'data_presenca']
    
    def __str__(self):
        return f"{self.aluno} - {self.data_presenca} - {self.get_status_display()}"


class Graduacao(models.Model):
    """Modelo para controle de graduações (faixas e graus)"""
    FAIXA_CHOICES = [
        ('BRANCA', 'Branca'),

        ('CINZA_BRANCA', 'Cinza e Branca'),
        ('CINZA', 'Cinza'),
        ('CINZA_PRETA', 'Cinza e Preta'),

        ('AMARELA_BRANCA', 'Amarela e Branca'),
        ('AMARELA', 'Amarela'),
        ('AMARELA_PRETA', 'Amarela e Preta'),

        ('LARANJA_BRANCA', 'Laranja e Branca'),
        ('LARANJA', 'Laranja'),
        ('LARANJA_PRETA', 'Laranja e Preta'),

        ('VERDE_BRANCA', 'Verde e Branca'),
        ('VERDE', 'Verde'),
        ('VERDE_PRETA', 'Verde e Preta'),

        ('AZUL', 'Azul'),
        ('ROXA', 'Roxa'),
        ('MARROM', 'Marrom'),
        ('PRETA', 'Preta'),
    ]
    
    aluno = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'group_role': 'STD'},
        related_name='graduacao'
    )
    faixa = models.CharField(
        'Faixa',
        max_length=15,
        choices=FAIXA_CHOICES,
        default='BRANCA'
    )
    grau = models.IntegerField(
        'Grau',
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        default=0
    )
    data_graduacao = models.DateField('Data da Graduação', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Graduação'
        verbose_name_plural = 'Graduações'
    
    def __str__(self):
        return f"{self.aluno} - {self.get_faixa_display()} - {self.grau}º grau"


class PlanoAula(models.Model):
    """Modelo para planos de aula"""
    titulo = models.CharField('Título', max_length=200)
    descricao = models.TextField('Descrição')
    professor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'group_role__in': ['PRO', 'ADM']},
        related_name='planos_aula'
    )
    data_inicio = models.DateField('Data de Início')
    data_fim = models.DateField('Data de Término', null=True, blank=True)
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='planos_aula',
        null=True,
        blank=True
    )
    ativo = models.BooleanField('Ativo', default=True) # pyright: ignore[reportArgumentType]
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Plano de Aula'
        verbose_name_plural = 'Planos de Aula'
        ordering = ['-data_inicio']
    
    def __str__(self):
        return f"{self.titulo} - {self.professor.first_name} {self.professor.last_name}"


class ItemPlanoAula(models.Model):
    """Modelo para itens individuais dentro de um plano de aula"""
    plano = models.ForeignKey(
        PlanoAula,
        on_delete=models.CASCADE,
        related_name='itens'
    )
    assunto = models.CharField('Assunto', max_length=200)
    data_aula = models.DateField('Data da Aula')
    ordem = models.IntegerField('Ordem', default=1) # pyright: ignore[reportArgumentType]
    
    class Meta:
        verbose_name = 'Item do Plano de Aula'
        verbose_name_plural = 'Itens do Plano de Aula'
        ordering = ['plano', 'data_aula', 'ordem']
    
    def __str__(self):
        return f"{self.plano} - {self.assunto}"


class Ranking(models.Model):
    """Modelo para controle de rankings"""
    TIPO_CHOICES = [
        ('FALTAS', 'Menos Faltas'),
        ('CAMPEONATO', 'Mini-Campeonato'),
        ('ALUNO_DESTAQUE', 'Aluno Destaque'),
    ]
    
    titulo = models.CharField('Título', max_length=200)
    tipo = models.CharField('Tipo', max_length=15, choices=TIPO_CHOICES)
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='rankings',
        null=True,
        blank=True
    )
    data_inicio = models.DateField('Data de Início')
    data_fim = models.DateField('Data de Término', null=True, blank=True)
    ativo = models.BooleanField('Ativo', default=True) # pyright: ignore[reportArgumentType]
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ranking'
        verbose_name_plural = 'Rankings'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.titulo} - {self.turma.nome if self.turma else 'Todas as Turmas'} - {self.get_tipo_display()}"


class PosicaoRanking(models.Model):
    """Modelo para posições dos alunos no ranking"""
    ranking = models.ForeignKey(
        Ranking,
        on_delete=models.CASCADE,
        related_name='posicoes'
    )
    aluno = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'group_role': 'STD'},
        related_name='posicoes_ranking'
    )
    posicao = models.IntegerField('Posição')
    pontuacao = models.FloatField('Pontuação', default=0) # pyright: ignore[reportArgumentType]
    
    class Meta:
        verbose_name = 'Posição no Ranking'
        verbose_name_plural = 'Posições no Ranking'
        ordering = ['ranking', 'posicao']
        unique_together = ['ranking', 'aluno']
    
    def __str__(self):
        return f"{self.ranking} - {self.aluno} - {self.posicao}º lugar"


class Pedido(models.Model):
    """Modelo para controle de pedidos (Kimonos, Faixas, etc.)"""
    TIPO_CHOICES = [
        ('KIMONO', 'Kimono'),
        ('FAIXA', 'Faixa'),
        ('HASHGUARD', 'Hashguard'),
        ('EXAME', 'Exame de Graduação'),
        ('TROCA_FAIXA', 'Troca de Faixa'),
    ]
    
    STATUS_CHOICES = [
        ('PEND', 'Pendente'),
        ('APRO', 'Aprovado'),
        ('REJE', 'Rejeitado'),
        ('ENTR', 'Entregue'),
    ]
    
    aluno = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'group_role': 'STD'},
        related_name='pedidos'
    )
    tipo = models.CharField('Tipo', max_length=11, choices=TIPO_CHOICES)
    descricao = models.TextField('Descrição', blank=True)
    status = models.CharField(
        'Status',
        max_length=4,
        choices=STATUS_CHOICES,
        default='PEND'
    )
    data_solicitacao = models.DateTimeField('Data de Solicitação', auto_now_add=True)
    data_aprovacao = models.DateTimeField('Data de Aprovação', null=True, blank=True)
    aprovado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'group_role__in': ['PRO', 'ADM']},
        related_name='pedidos_aprovados'
    )
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-data_solicitacao']
    
    def __str__(self):
        return f"{self.aluno} - {self.get_tipo_display()} - {self.get_status_display()}"
