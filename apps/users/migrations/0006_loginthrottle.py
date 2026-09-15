from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('users', '0005_user_phone')]

    operations = [
        migrations.CreateModel(
            name='LoginThrottle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=64, unique=True, verbose_name='Clave anónima')),
                ('scope', models.CharField(choices=[('ACCOUNT', 'Cuenta'), ('IP', 'Dirección IP')], max_length=10, verbose_name='Ámbito')),
                ('failures', models.PositiveIntegerField(default=0, verbose_name='Intentos fallidos')),
                ('window_started_at', models.DateTimeField(verbose_name='Inicio de ventana')),
                ('blocked_until', models.DateTimeField(blank=True, null=True, verbose_name='Bloqueado hasta')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última actualización')),
            ],
            options={
                'verbose_name': 'Límite de acceso',
                'verbose_name_plural': 'Límites de acceso',
            },
        ),
    ]
