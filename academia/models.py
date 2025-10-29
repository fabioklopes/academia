from django.db import models
from django.utils import timezone

class User(models.Model):
    # ... (código do modelo User inalterado) ...
    ACCESS_GROUP = (
        ('ADM', 'Administradores'),
        ('PRO', 'Professores'),
        ('STU', 'Alunos'),
    )

    BELTS = (
        ('WHITE', 'Branca'),
        
        ('GRAY_WHITE', 'Cinza / Branca'),
        ('GRAY', 'Cinza'),
        ('GRAY_BLACK', 'Cinza / Preta'),

        ('YELLOW_WHITE', 'Amarela / Branca'),
        ('YELLOW', 'Amarela'),
        ('YELLOW_BLACK', 'Amarela / Preta'),

        ('ORANGE_WHITE', 'Laranja / Branca'),
        ('ORANGE', 'Laranja'),
        ('ORANGE_BLACK', 'Laranja / Preta'),

        ('GREEN_WHITE', 'Verde / Branca'),
        ('GREEN', 'Verde'),
        ('GREEN_BLACK', 'Verde / Preta'),
        
        ('BLUE', 'Azul'),
        ('PURPLE', 'Roxa'),
        ('BROWN', 'Marrom'),
        ('BLACK', 'Preta'),
    )

    DEGREES = (
        ('0', 'Nenhum'),
        ('1', '1 Grau'),
        ('2', '2 Graus'),
        ('3', '3 Graus'),
        ('4', '4 Graus'),
        ('5', '5 Graus'),
        ('6', '6 Graus'),
    )

    first_name = models.CharField(max_length=45, blank=False, null=False)
    last_name = models.CharField(max_length=50, blank=False, null=False)
    identification = models.CharField(max_length=11, unique=True, blank=False, null=False)
    image_profile = models.ImageField(upload_to='profiles/', blank=True, null=True)
    birthday = models.DateField()
    email = models.CharField(max_length=80, unique=True, blank=False, null=False)
    keypass = models.CharField(max_length=255)
    access_group = models.CharField(max_length=3, choices=ACCESS_GROUP, blank=False, null=False, default='STU')
    phone = models.CharField(max_length=11, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    current_belt = models.CharField(max_length=20, choices=BELTS, blank=True, null=True)
    current_degree = models.CharField(max_length=1, choices=DEGREES, blank=True, null=True)
    status = models.IntegerField(default=1) # 1 para ativo, 0 para inativo
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return f"({self.access_group}) {self.first_name} {self.last_name}"

class Group_Role(models.Model):
    # ... (código do modelo Group_Role inalterado) ...
    name = models.CharField(max_length=25, unique=True, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    permissions = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Regra de Grupo'
        verbose_name_plural = 'Regras de Grupos'
    
    def __str__(self):
        return f"{self.name} - {self.description}"

class Class(models.Model):
    # ... (código do modelo Class inalterado) ...
    class_name = models.CharField(max_length=50, unique=True, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True, verbose_name='Turma ativa?')
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, limit_choices_to={'access_group': 'PRO'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
    
    def __str__(self):
        return f"{self.class_name} - {self.description}"

class AttendenceRequest(models.Model):
    STATUS_CHOICES = (
        ('PEN', 'Pendente'),
        ('APR', 'Aprovado'),
        ('REJ', 'Rejeitado'),
        ('CAN', 'Cancelado'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'access_group': 'STU'})
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, verbose_name="Turma")
    attendence_date = models.DateField(verbose_name="Data da Solicitação")
    reason = models.TextField(blank=True, null=True, verbose_name="Observação")
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='PEN')
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_requests', limit_choices_to={'access_group': 'PRO'})
    processed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Motivo da Rejeição")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Solicitação de Presença'
        verbose_name_plural = 'Solicitações de Presenças'
        ordering = ['-attendence_date']
    
    def __str__(self):
        return f"Solicitação de {self.student} para {self.class_obj} em {self.attendence_date}"
