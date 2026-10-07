from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('persona', '0002_alter_persona_domicilio_alter_persona_localidad_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='persona',
            name='sexo',
            field=models.CharField(
                blank=True,
                choices=[
                    ('m', 'Masculino'),
                    ('f', 'Femenino'),
                    ('o', 'Otro'),
                ],
                max_length=1,
                null=True,
                verbose_name='Sexo',
            ),
        ),
    ]
