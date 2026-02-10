# Generated manually to fix IntegrityError

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('academia', '0020_alter_graduacao_grau_solicitacaoalteracaograduacao'),
    ]

    operations = [
        # Remove the unique constraint that is causing the IntegrityError
        migrations.RunSQL(
            sql='ALTER TABLE "academia_graduacao" DROP CONSTRAINT IF EXISTS "academia_graduacao_aluno_id_091be1dd_uniq";',
            reverse_sql=migrations.RunSQL.noop
        ),
        # Remove the unique index if it exists
        migrations.RunSQL(
            sql='DROP INDEX IF EXISTS "academia_graduacao_aluno_id_091be1dd_uniq";',
            reverse_sql=migrations.RunSQL.noop
        ),
        # Ensure a standard index exists for the foreign key
        migrations.RunSQL(
            sql='CREATE INDEX IF NOT EXISTS "academia_graduacao_aluno_id_idx" ON "academia_graduacao" ("aluno_id");',
            reverse_sql='DROP INDEX IF EXISTS "academia_graduacao_aluno_id_idx";'
        ),
        # Re-affirm the field definition as ForeignKey (non-unique)
        migrations.AlterField(
            model_name='graduacao',
            name='aluno',
            field=models.ForeignKey(
                limit_choices_to={'group_role': 'STD'},
                on_delete=django.db.models.deletion.CASCADE,
                related_name='graduacoes',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
