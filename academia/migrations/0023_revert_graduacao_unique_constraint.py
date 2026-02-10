# Generated manually to revert unique constraint on Graduacao

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0022_add_graduacao_unique_constraint'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='graduacao',
            unique_together=set(),
        ),
    ]
