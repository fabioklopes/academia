from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import time
import os
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def photo_upload_to(instance, filename):
    timestamp = str(int(time.time()))
    # Force extension to be .png as per requirements
    ext = '.png'
    if instance.pk:
        # Final path
        return f'photos/{instance.pk}_{timestamp}{ext}'
    
    # Temporary path for new users, will be renamed in save()
    return f'photos/temp/{timestamp}_{filename}'

class User(AbstractUser):
    STATUS_CHOICES = [('ATIVO', 'Ativo'), ('INATIVO', 'Inativo'), ('PENDENTE', 'Pendente')]
    GROUP_ROLE_CHOICES = [('STD', 'Aluno'), ('PRO', 'Professor'), ('ADM', 'Administrador')]
    KIMONO_SIZE_CHOICES = [('A0', 'A0'), ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4'), ('A5', 'A5'), ('A6', 'A6')]
    BELT_SIZE_CHOICES = [('A0', 'A0'), ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4'), ('A5', 'A5'), ('A6', 'A6')]

    birthday = models.DateField('Data de Nascimento', null=True, blank=True)
    group_role = models.CharField('Perfil', max_length=3, choices=GROUP_ROLE_CHOICES, default='STD')
    status = models.CharField('Status', max_length=8, choices=STATUS_CHOICES, default='PENDENTE')
    photo = models.ImageField('Foto', upload_to=photo_upload_to, null=True, blank=True, default='photos/default_profile.png')
    height = models.IntegerField('Altura (cm)', null=True, blank=True)
    weight = models.IntegerField('Peso (kg)', null=True, blank=True)
    kimono_size = models.CharField('Tamanho do Kimono', max_length=2, choices=KIMONO_SIZE_CHOICES, null=True, blank=True)
    belt_size = models.CharField('Tamanho da Faixa', max_length=2, choices=BELT_SIZE_CHOICES, null=True, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=20, null=True, blank=True)
    responsible = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dependents')
    
    class Meta:
        verbose_name, verbose_name_plural = 'Usuário', 'Usuários'
        ordering = ['first_name', 'last_name']
    
    def save(self, *args, **kwargs):
        self.is_active = self.status == 'ATIVO'
        
        # Se a foto for removida (definida como None ou ''), redefina para o padrão.
        if not self.photo:
            self.photo = 'photos/default_profile.png'

        old_photo = None
        if self.pk:
            try:
                old_photo = User.objects.get(pk=self.pk).photo
            except User.DoesNotExist:
                pass

        if self.photo and self.photo != old_photo:
            try:
                if hasattr(self.photo, 'open'):
                    self.photo.open()
                if hasattr(self.photo, 'seek'):
                    self.photo.seek(0)
                    
                img = Image.open(self.photo)
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                target_width = 200
                target_height = 200
                
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

                output = BytesIO()
                
                img.save(output, format='PNG', optimize=True)
                
                if output.tell() > 1048576:
                    output = BytesIO()
                    img.save(output, format='PNG', quality=85, optimize=True)

                new_content = ContentFile(output.getvalue())
                
                timestamp = str(int(time.time()))
                new_name = f'{self.pk}_{timestamp}.png'
                new_content.name = new_name
                
                self.photo = new_content
            except Exception as e:
                # Não atribua o padrão aqui, pois o erro pode ser transitório
                # e não queremos perder a foto que o usuário tentou enviar.
                print(f"Error processing image: {e}")

        if old_photo and self.photo != old_photo and 'default_profile.png' not in old_photo.name:
            old_photo.delete(save=False)

        is_new = self.pk is None

        super().save(*args, **kwargs)

        if is_new and self.photo and 'photos/temp/' in self.photo.name:
            old_path = self.photo.path
            filename = os.path.basename(self.photo.name)
            
            new_name = photo_upload_to(self, filename)
            
            new_absolute_path = self.photo.storage.path(new_name)
            
            new_dir = os.path.dirname(new_absolute_path)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)
                
            if os.path.exists(old_path):
                os.rename(old_path, new_absolute_path)
                self.photo.name = new_name
                super().save(update_fields=['photo'])
        
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
    CLASS_TYPE_CHOICES = [('GI', 'Gi'), ('NOGI', 'No-Gi'), ('BOTH', 'Ambas')]

    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'group_role': 'STD'}, related_name='attendance_requests')
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='attendance_requests')
    attendance_date = models.DateField('Data da Presença')
    class_type = models.CharField('Tipo de Aula', max_length=4, choices=CLASS_TYPE_CHOICES, default='BOTH')
    reason = models.TextField('Motivo da Solicitação')
    status = models.CharField('Status', max_length=3, choices=STATUS_CHOICES, default='PEN')
    rejection_reason = models.TextField('Motivo da Rejeição', blank=True)
    processed_at = models.DateTimeField('Data de Processamento', null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'group_role__in': ['PRO', 'ADM']}, related_name='processed_requests')
    notified = models.BooleanField(default=False)

    class Meta:
        verbose_name, verbose_name_plural = 'Solicitação de Presença', 'Solicitações de Presença'
        ordering = ['-attendance_date']
        unique_together = ['student', 'turma', 'attendance_date', 'class_type']

    def __str__(self):
        return f"{self.student} - {self.attendance_date} - {self.get_status_display()}"

class Graduacao(models.Model):
    FAIXA_CHOICES = [
        ('WHITE', 'Branca'),
        ('GRAY_WHITE', 'Cinza e Branca'),
        ('GRAY', 'Cinza'),
        ('GRAY_BLACK', 'Cinza e Preta'),
        ('YELLOW_WHITE', 'Amarela e Branca'),
        ('YELLOW', 'Amarela'),
        ('YELLOW_BLACK', 'Amarela e Preta'),
        ('ORANGE_WHITE', 'Laranja e Branca'),
        ('ORANGE', 'Laranja'),
        ('ORANGE_BLACK', 'Laranja e Preta'),
        ('GREEN_WHITE', 'Verde e Branca'),
        ('GREEN', 'Verde'),
        ('GREEN_BLACK', 'Verde e Preta'),
        ('BLUE', 'Azul'),
        ('PURPLE', 'Roxa'),
        ('BROWN', 'Marrom'),
        ('BLACK', 'Preta'),
    ]
    
    aluno = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'group_role': 'STD'}, related_name='graduacoes')
    faixa = models.CharField('Faixa', max_length=20, choices=FAIXA_CHOICES)
    grau = models.IntegerField('Grau', validators=[MinValueValidator(0), MaxValueValidator(6)])
    data_graduacao = models.DateField('Data da Graduação')
    notified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name, verbose_name_plural = 'Graduação', 'Graduações'
        ordering = ['-data_graduacao']
    
    def __str__(self):
        return f"{self.aluno} - {self.get_faixa_display()} {self.grau}º grau"

class SolicitacaoAlteracaoGraduacao(models.Model):
    STATUS_CHOICES = [('PEND', 'Pendente'), ('APRO', 'Aprovado'), ('REJE', 'Rejeitado')]
    
    graduacao = models.ForeignKey(Graduacao, on_delete=models.CASCADE, related_name='solicitacoes_alteracao')
    nova_data = models.DateField('Nova Data')
    motivo_solicitacao = models.CharField('Motivo da Solicitação', max_length=50)
    status = models.CharField('Status', max_length=4, choices=STATUS_CHOICES, default='PEND')
    motivo_rejeicao = models.TextField('Motivo da Rejeição', blank=True, null=True)
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    processado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitacoes_graduacao_processadas')
    data_processamento = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitação de Alteração de Graduação'
        verbose_name_plural = 'Solicitações de Alteração de Graduação'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f"Solicitação de {self.graduacao.aluno} - {self.status}"

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

class Meta(models.Model):
    professor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'group_role__in': ['PRO', 'ADM']}, related_name='metas')
    titulo = models.CharField('Título', max_length=200)
    data_inicio = models.DateField('Data Início')
    data_fim = models.DateField('Data Fim')
    meta_aulas = models.IntegerField('Meta de Aulas (Qtd)')
    minimo_aulas = models.IntegerField('Mínimo de Aulas (Qtd)')
    minimo_frequencia = models.IntegerField('Frequência Mínima (%)')
    
    class Meta:
        verbose_name = 'Meta'
        verbose_name_plural = 'Metas'
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.titulo} - {self.professor.first_name}"

class Item(models.Model):
    TIPO_CHOICES = [('KIMONO', 'Kimono'), ('FAIXA', 'Faixa'), ('HASHGUARD', 'Hashguard'), ('TAXA', 'Taxa')]
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

class Log(models.Model):
    STATUS_CHOICES = [
        ('SUCESSO', 'Sucesso'),
        ('FALHA', 'Falha'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.TextField('Ação')
    timestamp = models.DateTimeField('Data e Hora', auto_now_add=True)
    status = models.CharField('Status', max_length=7, choices=STATUS_CHOICES, default='SUCESSO')

    class Meta:
        verbose_name = 'Log de Ação'
        verbose_name_plural = 'Logs de Ações'
        ordering = ['-timestamp']

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'Sistema'
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} {user_name} executou {self.action}"
