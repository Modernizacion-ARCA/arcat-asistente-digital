from django.db import migrations, models
import django.db.models.deletion
import pgvector.django.vector


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_enable_vector_extension'),
        ('sources', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentChunk',
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
                ('contenido', models.TextField()),
                ('indice', models.PositiveIntegerField()),
                (
                    'embedding',
                    pgvector.django.vector.VectorField(dimensions=1024),
                ),
                ('embedding_model', models.CharField(max_length=255)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                (
                    'documento',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='fragmentos',
                        to='sources.documento',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Fragmento de documento',
                'verbose_name_plural': 'Fragmentos de documentos',
                'ordering': ('documento_id', 'indice'),
                'indexes': [
                    models.Index(
                        fields=['embedding_model'],
                        name='chunk_embedding_model_idx',
                    ),
                ],
                'constraints': [
                    models.UniqueConstraint(
                        fields=('documento', 'indice'),
                        name='unique_chunk_index_por_documento',
                    ),
                ],
            },
        ),
    ]
