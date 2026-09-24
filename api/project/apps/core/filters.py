from django.contrib import admin


class PublicadoFilter(admin.SimpleListFilter):
    title = 'Publicado'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'publicado'

    def lookups(self, request, model_admin):
        return (
            ('true', 'Publicados'),
            ('false', 'No publicados'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.exclude(publicado__isnull=value == 'true')

        return queryset.all()
