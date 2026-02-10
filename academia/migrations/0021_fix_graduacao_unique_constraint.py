# This migration is superseded by 0021_remove_graduacao_aluno_unique
# Keeping it as a no-op to avoid file deletion issues if any.

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0021_remove_graduacao_aluno_unique'),
    ]

    operations = [
    ]
