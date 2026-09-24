# Generated for the ARCAT domain foundation.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Organismo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('url', models.URLField(blank=True, max_length=500)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Organismo', 'verbose_name_plural': 'Organismos', 'ordering': ('nombre',)},
        ),
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('organismo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='areas', to='organizations.organismo')),
            ],
            options={'verbose_name': 'Área', 'verbose_name_plural': 'Áreas', 'ordering': ('organismo__nombre', 'nombre')},
        ),
        migrations.AddConstraint(
            model_name='area',
            constraint=models.UniqueConstraint(fields=('organismo', 'nombre'), name='unique_area_por_organismo'),
        ),
    ]
