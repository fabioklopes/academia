from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0014_fix_unique_constraint'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200, verbose_name='Título')),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(verbose_name='Data Fim')),
                ('meta_aulas', models.IntegerField(verbose_name='Meta de Aulas (Qtd)')),
                ('minimo_aulas', models.IntegerField(verbose_name='Mínimo de Aulas (Qtd)')),
                ('minimo_frequencia', models.IntegerField(verbose_name='Frequência Mínima (%)')),
                ('professor', models.ForeignKey(limit_choices_to={'group_role__in': ['PRO', 'ADM']}, on_delete=django.db.models.deletion.CASCADE, related_name='metas', to='academia.user')),
            ],
            options={
                'verbose_name': 'Meta',
                'verbose_name_plural': 'Metas',
                'ordering': ['-data_inicio'],
            },
        ),
    ]
