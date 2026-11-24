"""Workflow del legajo (SRS RF-CORE-003): qué transiciones se permiten y cuáles no."""
from datetime import date

import pytest

from src.inscripcion.domain.entities import (
    TRANSICIONES_PERMITIDAS,
    EstadoLegajo,
    Legajo,
    TipoCarrera,
    TransicionInvalida,
    numero_de_legajo,
    prefijo_de_legajo,
)
from src.inscripcion.domain.value_objects import DNI, Email

E = EstadoLegajo


def legajo_en(estado: EstadoLegajo) -> Legajo:
    return Legajo(
        id="1",
        numero_legajo="P-00000001",
        cohorte_id="c",
        dni=DNI("35222111"),
        apellido="Rodríguez",
        nombre="Ana",
        email=Email("ana@mail.com"),
        tipo_carrera=TipoCarrera("Maestria"),
        solicita_beca=False,
        estado=estado,
    )


@pytest.mark.parametrize("desde, hacia", [
    (E.BORRADOR, E.PENDIENTE),          # el aspirante envía
    (E.PENDIENTE, E.EN_REVISION),       # la coordinación lo toma
    (E.PENDIENTE, E.OBSERVADO),
    (E.EN_REVISION, E.OBSERVADO),
    (E.OBSERVADO, E.PENDIENTE),         # corrige y reenvía
    (E.EN_REVISION, E.COMPLETADO),      # aprobar
    (E.EN_REVISION, E.RECHAZADO),
    (E.COMPLETADO, E.ACTIVO),           # matricular
    (E.COMPLETADO, E.VENCIDO),          # BR-005
    (E.COMPLETADO, E.BAJA),
    (E.ACTIVO, E.BAJA),
])
def test_transiciones_permitidas(desde, hacia):
    legajo = legajo_en(desde)
    legajo.transicionar_a(hacia)
    assert legajo.estado == hacia


@pytest.mark.parametrize("desde, hacia", [
    (E.BORRADOR, E.COMPLETADO),         # no se puede aprobar sin enviar
    (E.PENDIENTE, E.COMPLETADO),        # no se puede aprobar sin revisar
    (E.PENDIENTE, E.ACTIVO),
    (E.OBSERVADO, E.EN_REVISION),       # primero tiene que reenviar
    (E.EN_REVISION, E.ACTIVO),          # no se matricula sin aprobar
    (E.RECHAZADO, E.PENDIENTE),         # estado terminal
    (E.VENCIDO, E.ACTIVO),
    (E.BAJA, E.ACTIVO),
])
def test_transiciones_prohibidas(desde, hacia):
    legajo = legajo_en(desde)
    with pytest.raises(TransicionInvalida, match=f"No se puede pasar de {desde.value} a {hacia.value}"):
        legajo.transicionar_a(hacia)
    assert legajo.estado == desde  # No cambia


def test_todos_los_estados_tienen_reglas():
    assert set(TRANSICIONES_PERMITIDAS) == set(EstadoLegajo)


@pytest.mark.parametrize("estado", [E.RECHAZADO, E.VENCIDO, E.BAJA, E.GRADUADO])
def test_estados_terminales(estado):
    assert legajo_en(estado).es_estado_terminal()


def test_estado_no_terminal():
    assert not legajo_en(E.PENDIENTE).es_estado_terminal()


@pytest.mark.parametrize("estado, puede", [
    (E.BORRADOR, True), (E.OBSERVADO, True),
    (E.PENDIENTE, False), (E.EN_REVISION, False), (E.COMPLETADO, False), (E.ACTIVO, False),
])
def test_solo_se_edita_en_borrador_u_observado(estado, puede):
    assert legajo_en(estado).puede_editar_formulario() is puede


def test_reserva_de_vacante_vence_a_los_30_dias():
    """BR-005."""
    assert Legajo.vencimiento_de_reserva(date(2026, 11, 10)) == date(2026, 12, 10)
    assert Legajo.vencimiento_de_reserva(date(2026, 12, 15)) == date(2027, 1, 14)


def test_formato_del_numero_de_legajo():
    """SRS: "26-001-045" → año 2026, cohorte 1, estudiante 45."""
    assert numero_de_legajo(2026, 1, 45) == "26-001-045"
    assert numero_de_legajo(2027, 2, 1) == "27-002-001"
    assert prefijo_de_legajo(2030, 12) == "30-012-"