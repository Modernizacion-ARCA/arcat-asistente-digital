from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('sources', '0002_documentchunk'),
    ]

    operations = [
        migrations.CreateModel(
            name='KnowledgeUpdateRun',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'estado',
                    models.CharField(
                        choices=[
                            ('EN_CURSO', 'En curso'),
                            ('EXITOSA', 'Exitosa'),
                            ('ERROR', 'Con errores'),
                        ],
                        db_index=True,
                        default='EN_CURSO',
                        max_length=10,
                    ),
                ),
                ('fuentes_total', models.PositiveIntegerField(default=0)),
                ('documentos_actualizados', models.PositiveIntegerField(default=0)),
                ('documentos_sin_cambios', models.PositiveIntegerField(default=0)),
                ('documentos_indexados', models.PositiveIntegerField(default=0)),
                ('errores', models.PositiveIntegerField(default=0)),
                ('detalle_errores', models.JSONField(blank=True, default=list)),
                ('fecha_inicio', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('fecha_fin', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Actualización de conocimiento',
                'verbose_name_plural': 'Actualizaciones de conocimiento',
                'ordering': ('-fecha_inicio',),
            },
        ),
    ]
