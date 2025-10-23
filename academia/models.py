from django.db import models

class User(models.Model):
    first_name = models.CharField(max_length=45), 
    last_name = models.CharField(max_length=50),
    identification = models.CharField(max_length=11, unique=True, blank=False, null=False)
    birthday = models.DateField(),
    email = models.CharField(max_length=80, unique=True, blank=False, null=False)
    keypass = models.CharField(max_length=255)
    access_role = models.CharField(max_length=1, default='U')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuário',
        verbose_name_plural = 'Usuários'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


