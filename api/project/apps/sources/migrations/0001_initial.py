# Generated for the ARCAT domain foundation.
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = [('organizations', '0001_initial'), ('procedures', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='Fuente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250)),
                ('url', models.URLField(max_length=1000, unique=True)),
                ('tipo', models.CharField(choices=[('SITIO_WEB', 'Sitio web'), ('PORTAL_TRAMITES', 'Portal de trámites'), ('BOLETIN_OFICIAL', 'Boletín oficial'), ('REPOSITORIO', 'Repositorio documental'), ('OTRO', 'Otro')], max_length=30)),
                ('origen_informacion', models.CharField(choices=[('OFICIAL', 'Oficial'), ('DEMO', 'Demo')], max_length=10)),
                ('prioridad', models.PositiveSmallIntegerField(default=100)),
                ('estado_verificacion', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('VERIFICADA', 'Verificada'), ('RECHAZADA', 'Rechazada')], default='PENDIENTE', max_length=20)),
                ('fecha_ultima_consulta', models.DateTimeField(blank=True, null=True)),
                ('fecha_actualizacion_origen', models.DateTimeField(blank=True, null=True)),
                ('estado_disponibilidad', models.CharField(choices=[('DISPONIBLE', 'Disponible'), ('NO_DISPONIBLE', 'No disponible'), ('DESCONOCIDO', 'Desconocido')], default='DESCONOCIDO', max_length=20)),
                ('activo', models.BooleanField(default=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('categoria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='fuentes', to='procedures.categoria')),
                ('organismo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fuentes', to='organizations.organismo')),
                ('plataforma', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='fuentes', to='procedures.plataforma')),
            ],
            options={'verbose_name': 'Fuente', 'verbose_name_plural': 'Fuentes', 'ordering': ('prioridad', 'nombre')},
        ),
        migrations.CreateModel(
            name='Documento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=300)),
                ('tipo', models.CharField(choices=[('PDF', 'PDF'), ('HTML', 'HTML'), ('INSTRUCTIVO', 'Instructivo'), ('FORMULARIO', 'Formulario'), ('NORMATIVA', 'Normativa'), ('GUIA', 'Guía'), ('MANUAL', 'Manual'), ('OTRO', 'Otro')], max_length=20)),
                ('url', models.URLField(max_length=1000)),
                ('fecha_documento', models.DateField(blank=True, null=True)),
                ('contenido', models.TextField(blank=True)),
                ('texto_extraido', models.TextField(blank=True)),
                ('checksum', models.CharField(blank=True, db_index=True, max_length=64, validators=[django.core.validators.RegexValidator(message='El checksum debe ser un hash SHA-256 hexadecimal.', regex='^[0-9a-f]{64}$')])),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('fuente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='documentos', to='sources.fuente')),
                ('servicios', models.ManyToManyField(blank=True, related_name='documentos', to='procedures.servicio')),
                ('tramites', models.ManyToManyField(blank=True, related_name='documentos', to='procedures.tramite')),
            ],
            options={'verbose_name': 'Documento', 'verbose_name_plural': 'Documentos', 'ordering': ('titulo',)},
        ),
        migrations.AddConstraint(
            model_name='documento',
            constraint=models.UniqueConstraint(fields=('fuente', 'url'), name='unique_documento_por_fuente_url'),
        ),
    ]
