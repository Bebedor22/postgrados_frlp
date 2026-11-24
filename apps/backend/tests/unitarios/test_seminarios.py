"""Tests puros del dominio del Módulo B: notas, estados y progreso."""
import pytest

from src.carga_academica.domain.entities import (
    EstadoSeminario,
    InscripcionSeminario,
    ProgresoSeminarios,
    ReglaAcademicaViolada,
    Seminario,
    validar_nota,
)


def _seminario(**cambios) -> Seminario:
    base = dict(
        id="s1", carrera_id="c1", nombre="Metodología", codigo="met-01", horas_catedra=60
    )
    base.update(cambios)
    return Seminario(**base)


def _inscripcion(**cambios) -> InscripcionSeminario:
    base = dict(id="i1", legajo_id="l1", seminario_id="s1")
    base.update(cambios)
    return InscripcionSeminario(**base)


# ── Notas (RF-DOC-003 / BR-003) ──────────────────────────────────────────────

def test_nota_valida_de_1_a_10_con_un_decimal():
    assert validar_nota(4) == 4.0
    assert validar_nota(4.5) == 4.5
    assert validar_nota(10) == 10.0


@pytest.mark.parametrize("nota", [0, 11, 4.55, -1])
def test_nota_invalida_lanza_regla(nota: float):
    with pytest.raises(ReglaAcademicaViolada):
        validar_nota(nota)


def test_con_nota_mayor_o_igual_a_4_queda_aprobado():
    assert _inscripcion().registrar_nota(4).estado == EstadoSeminario.APROBADO


def test_con_nota_menor_a_4_queda_desaprobado():
    assert _inscripcion().registrar_nota(3.9).estado == EstadoSeminario.DESAPROBADO


def test_aprobado_sin_nota_no_es_valido():
    with pytest.raises(ReglaAcademicaViolada):
        _inscripcion(estado=EstadoSeminario.APROBADO, nota_final=None)


def test_asistencias_negativas_no_son_validas():
    with pytest.raises(ReglaAcademicaViolada):
        _inscripcion(asistencias=-1)


# ── Seminario ────────────────────────────────────────────────────────────────

def test_seminario_normaliza_nombre_y_codigo():
    seminario = _seminario(nombre="  Metodología  ", codigo="  met-01  ")
    assert seminario.nombre == "Metodología"
    assert seminario.codigo == "MET-01"
    assert seminario.es_obligatorio is True


def test_seminario_rechaza_horas_negativas():
    with pytest.raises(ReglaAcademicaViolada):
        _seminario(horas_catedra=-2)


def test_seminario_rechaza_codigo_vacio():
    with pytest.raises(ReglaAcademicaViolada):
        _seminario(codigo="   ")


# ── Progreso (insumo del semáforo) ───────────────────────────────────────────

def test_adeudados_es_la_diferencia_con_cero_piso():
    assert ProgresoSeminarios(obligatorios_total=8, aprobados=6).adeudados == 2
    assert ProgresoSeminarios(obligatorios_total=5, aprobados=6).adeudados == 0
