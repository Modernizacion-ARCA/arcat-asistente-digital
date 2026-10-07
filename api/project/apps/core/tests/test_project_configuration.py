from pathlib import Path

from django.conf import settings

from core.apps import CoreConfig


def test_primary_key_defaults_are_explicit():
    assert settings.DEFAULT_AUTO_FIELD == 'django.db.models.AutoField'
    assert CoreConfig.default_auto_field == 'django.db.models.BigAutoField'


def test_staticfiles_directories_exist():
    assert settings.STATICFILES_DIRS
    assert all(Path(directory).is_dir() for directory in settings.STATICFILES_DIRS)
