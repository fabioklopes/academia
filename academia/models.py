from django.db import models

class User(models.Model):

    ACCESS_GROUP = (
        ('ADM', 'Administradores'),
        ('PRO', 'Professores'),
        ('STU', 'Alunos'),
    )

    BELTS = (
        ('Branca', 'Branca'),
        
        ('CinzaBranca', 'Cinza / Branca'),
        ('Cinza', 'Cinza'),
        ('CinzaPreta', 'Cinza / Preta'),

        ('AmarelaBranca', 'Amarela / Branca'),
        ('Amarela', 'Amarela'),
        ('AmarelaPreta', 'Amarela / Preta'),

        ('LaranjaBranca', 'Laranja / Branca'),
        ('Laranja', 'Laranja'),
        ('LaranjaPreta', 'Laranja / Preta'),

        ('VerdeBranca', 'Verde / Branca'),
        ('Verde', 'Verde'),
        ('VerdePreta', 'Verde / Preta'),
        
        ('Azul', 'Azul'),
        ('Roxa', 'Roxa'),
        ('Marrom', 'Marrom'),
        ('Preta', 'Preta'),
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return f"({self.access_group}) {self.first_name} {self.last_name}"


class Group_Role(models.Model):
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
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'access_group': 'STU'})
    attendence_date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    attendence_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='attendence_by', limit_choices_to={'access_group': 'PRO'})

    class Meta:
        verbose_name = 'Solicitação de Presença'
        verbose_name_plural = 'Solicitações de Presenças'
    
    def __str__(self):
        return f"Presença de {self.student} em {self.attendence_date}"


class AttendenceAproval(models.Model):
    attendence_request = models.ForeignKey(AttendenceRequest, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    approval_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aprovação de Presença'
        verbose_name_plural = 'Aprovações de Presenças'
    
    def __str__(self):
        status = "Aprovado" if self.approved else "Rejeitado"
        return f"{status} - {self.attendence_request}"