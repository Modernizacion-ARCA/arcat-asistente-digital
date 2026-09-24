from django.db.models import QuerySet


class PublicadoQuerySet(QuerySet):
    def obtener_publicados(self):
        return self.filter(publicado__isnull=False)
