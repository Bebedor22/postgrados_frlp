"""Regla: solo un legajo ACTIVO puede tener TFI/Tesis."""
import pytest

from src.inscripcion.domain.entities import EstadoLegajo
from src.seguimiento_graduacion.application.gestionar_trabajos_finales import exigir_legajo_activo
from src.seguimiento_graduacion.domain.trabajo_final import LegajoNoActivo, ReglaTrabajoFinalViolada


def test_legajo_activo_pasa():
    exigir_legajo_activo(EstadoLegajo.ACTIVO)


@pytest.mark.parametrize("estado", [e for e in EstadoLegajo if e != EstadoLegajo.ACTIVO])
def test_cualquier_otro_estado_se_rechaza(estado):
    with pytest.raises(LegajoNoActivo) as error:
        exigir_legajo_activo(estado)
    assert estado.value in str(error.value)
    assert isinstance(error.value, ReglaTrabajoFinalViolada)  # el router lo traduce a 422
