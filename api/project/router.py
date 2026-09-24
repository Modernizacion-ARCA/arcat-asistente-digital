from rest_framework.routers import DefaultRouter

from persona import api as api_persona
from usuario import api as api_usuario


router = DefaultRouter()

router.register('persona', api_persona.PersonaViewSet, basename='persona')
router.register('usuario', api_usuario.UsuarioViewSet, basename='usuario')

