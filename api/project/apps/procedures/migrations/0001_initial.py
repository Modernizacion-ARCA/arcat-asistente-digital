# Generated for the ARCAT domain foundation.
from django.db import migrations, models
import django.db.models.deletion


MODALIDADES = [('ONLINE', 'En línea'), ('PRESENCIAL', 'Presencial'), ('MIXTA', 'Mixta'), ('NO_INFORMADA', 'No informada')]
TIPOS_SERVICIO = [('CONSULTA_DEUDA', 'Consulta de deuda'), ('PAGO', 'Pago de impuestos'), ('VENCIMIENTOS', 'Consulta de vencimientos'), ('BOLETA', 'Generación de boleta'), ('LIBRE_DEUDA', 'Libre deuda'), ('OTRO', 'Otro')]


def gestion_fields():
    return [
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('nombre', models.CharField(max_length=250)),
        ('slug', models.SlugField(max_length=270, unique=True)),
        ('descripcion', models.TextField()),
        ('requisitos', models.TextField(blank=True)),
        ('documentacion', models.TextField(blank=True)),
        ('pasos', models.TextField(blank=True)),
        ('costo', models.TextField(blank=True)),
        ('plazo', models.TextField(blank=True)),
        ('modalidad', models.CharField(choices=MODALIDADES, default='NO_INFORMADA', max_length=20)),
        ('autenticacion_requerida', models.BooleanField(default=False)),
        ('metodo_autenticacion', models.CharField(blank=True, max_length=200)),
        ('url_inicio', models.URLField(blank=True, max_length=500)),
        ('url_instructivo', models.URLField(blank=True, max_length=500)),
        ('observaciones', models.TextField(blank=True)),
        ('activo', models.BooleanField(default=True)),
        ('fecha_publicacion', models.DateField(blank=True, null=True)),
        ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
        ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
        ('area', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)ss', to='organizations.area')),
        ('categoria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)ss', to='procedures.categoria')),
        ('organismo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='%(class)ss', to='organizations.organismo')),
        ('plataforma', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='%(class)ss', to='procedures.plataforma')),
    ]


class Migration(migrations.Migration):
    initial = True
    dependencies = [('organizations', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120, unique=True)),
                ('slug', models.SlugField(max_length=140, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={'verbose_name': 'Categoría', 'verbose_name_plural': 'Categorías', 'ordering': ('nombre',)},
        ),
        migrations.CreateModel(
            name='Plataforma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('url', models.URLField(blank=True, max_length=500)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={'verbose_name': 'Plataforma', 'verbose_name_plural': 'Plataformas', 'ordering': ('nombre',)},
        ),
        migrations.CreateModel(
            name='Tramite',
            fields=gestion_fields() + [('tipo', models.CharField(blank=True, max_length=120))],
            options={'verbose_name': 'Trámite', 'verbose_name_plural': 'Trámites', 'ordering': ('nombre',)},
        ),
        migrations.CreateModel(
            name='Servicio',
            fields=gestion_fields() + [
                ('tipo', models.CharField(choices=TIPOS_SERVICIO, default='OTRO', max_length=30)),
                ('impuesto', models.CharField(blank=True, max_length=150)),
                ('conceptos_disponibles', models.TextField(blank=True)),
                ('consulta_deuda', models.TextField(blank=True)),
                ('generacion_boleta', models.TextField(blank=True)),
                ('medios_pago', models.TextField(blank=True)),
                ('instrucciones', models.TextField(blank=True)),
            ],
            options={'verbose_name': 'Servicio', 'verbose_name_plural': 'Servicios', 'ordering': ('nombre',)},
        ),
    ]
