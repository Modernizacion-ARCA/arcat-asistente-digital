from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    persona = models.ForeignKey(
        'persona.Persona',
        on_delete=models.SET_NULL,
        blank=True, null=True,
    )


    def __str__(self):
        return f'{self.username} ({self.persona or "sin persona"})'


    @staticmethod
    def autocomplete_search_fields():
        return 'first_name', 'last_name'
