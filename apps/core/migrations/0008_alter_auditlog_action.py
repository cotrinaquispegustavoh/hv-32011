from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('core', '0007_institutionalannouncement_event_date')]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('CREATE', 'Creación'),
                    ('UPDATE', 'Actualización'),
                    ('DELETE', 'Eliminación Lógica'),
                    ('HARD_DELETE', 'Eliminación Física'),
                    ('RESTORE', 'Restauración'),
                    ('LOGIN', 'Inicio de Sesión'),
                    ('LOGIN_BLOCKED', 'Acceso bloqueado'),
                    ('LOGOUT', 'Cierre de Sesión'),
                    ('PERMISSIONS', 'Cambio de Permisos'),
                ],
                max_length=15,
                verbose_name='Acción',
            ),
        ),
    ]
