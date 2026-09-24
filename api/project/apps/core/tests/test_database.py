import pytest
from django.db import connection


@pytest.mark.django_db
def test_vector_extension_is_available_on_postgresql():
    if connection.vendor != 'postgresql':
        pytest.skip('pgvector is validated only against the PostgreSQL test database')

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        assert cursor.fetchone() == (1,)
