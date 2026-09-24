"""settings URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView
from oauth2_provider.urls import base_urlpatterns
from django.urls import path, include
from project.router import router
from usuario.api import RegistroUsuarioAPIView
from django.conf import settings

admin.site.site_header = getattr(settings, 'PROJECT_NAME_HEADER')
admin.site.site_title = getattr(settings, 'PROJECT_NAME_TITLE')

urlpatterns = [
                  path(
                      '',
                      RedirectView.as_view(
                          url=f'{settings.FORCE_SCRIPT_NAME}/admin/' if settings.FORCE_SCRIPT_NAME else '/admin/'
                      )
                  ),
                  path('jet/', include('jet.urls', 'jet')),  # Django JET URLS

                  path('admin/', admin.site.urls),
                  path('oauth2/', include((base_urlpatterns, 'oauth2_provider'), namespace='oauth2_provider')),
                  path('auth/', include('rest_framework_social_oauth2.urls', namespace='auth-api')),
                  path('api/v1/usuario/registro/', RegistroUsuarioAPIView.as_view(), name='registro_usuario'),
                  path('api/v1/', include(router.urls)),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ACTIVAR_HERRAMIENTAS_DEBUGGING:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
