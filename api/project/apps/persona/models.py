from django.db import models


class Persona(models.Model):
    class Meta:
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'
        ordering = ['-id']

    MASCULINO = 'm'
    FEMENINO = 'f'
    OTRO = 'o'

    GENERO = (
        (MASCULINO, 'Masculino'),
        (FEMENINO, 'Femenino'),
        (OTRO, 'Otro')
    )
    nombre = models.CharField(max_length=30, verbose_name='Nombre')
    apellido = models.CharField(max_length=30, verbose_name='Apellido')
    documento_identidad = models.CharField(max_length=12, verbose_name='Documento Identidad', unique=True)
    fecha_nacimiento = models.DateField(verbose_name='Fecha de Nacimiento', blank=True, null=True)
    nacionalidad = models.ForeignKey('util.Ubicacion', on_delete=models.CASCADE,
                                     related_name='%(app_label)s_%(class)s_nacionalidad', blank=True, null=True)
    cuit = models.CharField(max_length=15, verbose_name='CUIL/CUIT', unique=True)
    localidad = models.ForeignKey('util.Ubicacion', on_delete=models.CASCADE,
                                  related_name='%(app_label)s_%(class)s_localidad', blank=True, null=True)
    domicilio = models.CharField(max_length=100, verbose_name='Domicilio', blank=True, null=True)
    sexo = models.CharField(max_length=1, choices=GENERO, verbose_name='Sexo', blank=True, null=True)
    # ocupacion
    @staticmethod
    def autocomplete_search_fields():
        return 'nombre', 'apellido'

    def __str__(self):
        return self.obtener_nombre_completo()

    def obtener_nombre_completo(self):
        nombre_completo = f'{self.apellido}, {self.nombre}'
        return nombre_completo.strip()

    obtener_nombre_completo.short_description = 'Nombre Completo'



