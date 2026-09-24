from django.db import models


class Organismo(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True)
    url = models.URLField(max_length=500, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('nombre',)
        verbose_name = 'Organismo'
        verbose_name_plural = 'Organismos'

    def __str__(self):
        return self.nombre


class Area(models.Model):
    organismo = models.ForeignKey(
        Organismo,
        on_delete=models.PROTECT,
        related_name='areas',
    )
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('organismo__nombre', 'nombre')
        constraints = [
            models.UniqueConstraint(
                fields=('organismo', 'nombre'),
                name='unique_area_por_organismo',
            ),
        ]
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'

    def __str__(self):
        return f'{self.organismo}: {self.nombre}'
