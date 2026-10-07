from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0001_enable_vector_extension')]

    operations = [
        migrations.CreateModel(
            name='LLMDailyQuota',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(unique=True)),
                ('solicitudes', models.PositiveIntegerField(default=0)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Cupo diario LLM',
                'verbose_name_plural': 'Cupos diarios LLM',
                'ordering': ('-fecha',),
            },
        ),
        migrations.CreateModel(
            name='LLMRequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proveedor', models.CharField(max_length=50)),
                ('modelo', models.CharField(max_length=255)),
                ('estado', models.CharField(choices=[('EXITOSA', 'Exitosa'), ('ERROR', 'Error'), ('BLOQUEADA', 'Bloqueada')], max_length=12)),
                ('posicion_fallback', models.PositiveSmallIntegerField(default=0)),
                ('tokens_entrada', models.PositiveIntegerField(blank=True, null=True)),
                ('tokens_salida', models.PositiveIntegerField(blank=True, null=True)),
                ('duracion_ms', models.PositiveIntegerField(default=0)),
                ('codigo_error', models.CharField(blank=True, max_length=100)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name': 'Solicitud LLM',
                'verbose_name_plural': 'Solicitudes LLM',
                'ordering': ('-fecha_creacion',),
            },
        ),
    ]
