# Generated manually to add unique constraint to Graduacao

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0021_fix_graduacao_unique_constraint'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='graduacao',
            unique_together={('aluno', 'faixa', 'grau')},
        ),
    ]
