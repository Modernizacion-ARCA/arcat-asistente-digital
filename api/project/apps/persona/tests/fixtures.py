import pytest

from persona.models import Persona


@pytest.fixture
def crear_personas():
    martin_miranda, _ = Persona.objects.get_or_create(
        nombre='Martín',
        apellido='Miranda',
        cuil='20326288307',
        documento_identidad='32628830'
    )

    david_sanchez, _ = Persona.objects.get_or_create(
        nombre='David',
        apellido='Sanchez Motran',
        cuil='27399353115',
        documento_identidad='39935311'
    )

    franco_zurita, _ = Persona.objects.get_or_create(
        nombre='Franco',
        apellido='Zurita',
        cuil='20324567897',
        documento_identidad='32456789'
    )

    return martin_miranda, david_sanchez, franco_zurita


