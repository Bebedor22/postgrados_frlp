"""Tests puros del semáforo (RF-GRAD-002) y de las métricas (RF-REP-001)."""
from datetime import date, timedelta

import pytest

from src.analytics.domain.metricas import (
    CohorteInfo,
    LegajoMetrica,
    calcular_dashboard,
)
from src.seguimiento_graduacion.domain.semaforo import (
    DatosSemaforo,
    EstadoSemaforo,
    calcular_semaforo,
)
from src.seguimiento_graduacion.domain.trabajo_final import (
    ReglaTrabajoFinalViolada,
    TrabajoFinal,
    TipoTrabajoFinal,
)

INICIO = date(2026, 4, 1)


def _datos(tipo: str, dias: int, **cambios) -> DatosSemaforo:
    base = dict(
        tipo_carrera=tipo,
        fecha_inscripcion=INICIO,
        seminarios_obligatorios_total=8,
        seminarios_aprobados=8,
        tiene_tfi_registrado=True,
        tiene_director_asignado=True,
        tiene_fecha_cpr=True,
        hoy=INICIO + timedelta(days=dias),
    )
    base.update(cambios)
    return DatosSemaforo(**base)


def test_especializacion_rojo_pasado_el_75pct_si_adeuda_seminarios():
    datos = _datos("Especializacion", 550, seminarios_aprobados=6)
    assert calcular_semaforo(datos) == EstadoSemaforo.ROJO


def test_especializacion_amarillo_si_no_inicio_tfi_despues_del_50pct():
    datos = _datos("Especializacion", 400, tiene_tfi_registrado=False)
    assert calcular_semaforo(datos) == EstadoSemaforo.AMARILLO


def test_especializacion_verde_si_esta_al_dia():
    datos = _datos("Especializacion", 200, seminarios_aprobados=3, tiene_tfi_registrado=False)
    assert calcular_semaforo(datos) == EstadoSemaforo.VERDE


def test_maestria_rojo_despues_del_80pct_si_adeuda_seminarios():
    datos = _datos("Maestria", 900, seminarios_aprobados=7)
    assert calcular_semaforo(datos) == EstadoSemaforo.ROJO


def test_maestria_amarillo_sin_director_despues_del_50pct():
    datos = _datos("Maestria", 600, tiene_director_asignado=False)
    assert calcular_semaforo(datos) == EstadoSemaforo.AMARILLO


def test_doctorado_rojo_sin_fecha_cpr_despues_del_70pct():
    datos = _datos("Doctorado", 1300, tiene_fecha_cpr=False)
    assert calcular_semaforo(datos) == EstadoSemaforo.ROJO


def test_doctorado_amarillo_sin_director_despues_del_40pct():
    datos = _datos("Doctorado", 800, tiene_director_asignado=False)
    assert calcular_semaforo(datos) == EstadoSemaforo.AMARILLO


def test_sin_fecha_de_inscripcion_queda_verde():
    assert calcular_semaforo(_datos("Maestria", 1000, fecha_inscripcion=None)) == EstadoSemaforo.VERDE


def _legajo(estado: str, semaforo: str = "VERDE", cohorte_id: str = "c1", **kwargs) -> LegajoMetrica:
    base = dict(
        legajo_id="l",
        cohorte_id=cohorte_id,
        cohorte_nombre="2026-1",
        cohorte_anio=2026,
        carrera_nombre="Maestría",
        tipo_carrera="Maestria",
        estado=estado,
        semaforo=semaforo,
    )
    base.update(kwargs)
    return LegajoMetrica(**base)


def test_metricas_retencion_desgranamiento_y_promedio_de_graduacion():
    legajos = [
        _legajo("ACTIVO", semaforo="ROJO"),
        _legajo("ACTIVO"),
        _legajo("GRADUADO", fecha_inscripcion=date(2024, 1, 1), fecha_graduacion=date(2026, 1, 1)),
        _legajo("BAJA"),
    ]
    dashboard = calcular_dashboard(legajos, [CohorteInfo(id="c1", nombre="2026-1", anio=2026)])
    cohorte = dashboard.cohortes[0]
    assert dashboard.total_inscriptos == 4
    assert dashboard.en_riesgo == 1
    assert cohorte.retencion_pct == 75.0
    assert cohorte.desgranamiento_pct == 25.0
    assert cohorte.tiempo_promedio_graduacion_dias == 731.0


def test_metricas_incluyen_cohortes_sin_inscriptos():
    dashboard = calcular_dashboard([], [CohorteInfo(id="c1", nombre="2027-1", anio=2027)])
    assert dashboard.total_inscriptos == 0
    assert dashboard.cohortes[0].inscriptos == 0
    assert dashboard.cohortes[0].retencion_pct == 0.0


def test_trabajo_final_valida_tipo_y_director():
    with pytest.raises(ReglaTrabajoFinalViolada):
        TrabajoFinal(
            id="t", legajo_id="l", tipo="TESINA", titulo="Un título",
            director_nombre="Directora", director_email="d@utn.edu.ar",
        )
    trabajo = TrabajoFinal(
        id="t", legajo_id="l", tipo="TFI", titulo="Un título",
        director_nombre="Directora", director_email="d@utn.edu.ar",
    )
    assert trabajo.tipo == TipoTrabajoFinal.TFI
    assert not trabajo.aprobado_por_cpr()


def test_excel_incluye_filtros_y_usuario_en_metadatos():
    from io import BytesIO

    from openpyxl import load_workbook

    from src.analytics.infrastructure.exportador_excel import exportar_dashboard_a_excel

    metricas = calcular_dashboard(
        [_legajo("ACTIVO")], [CohorteInfo(id="c1", nombre="2026-1", anio=2026)]
    )
    libro = load_workbook(BytesIO(exportar_dashboard_a_excel(
        metricas, filtros="Tipo de carrera: Maestria", usuario="coord@utn.test"
    )))
    assert libro.sheetnames == ["Resumen", "Cohortes", "Metadatos"]
    valores = {fila[0].value: fila[1].value for fila in libro["Metadatos"].iter_rows(min_row=2)}
    assert valores["Filtros aplicados"] == "Tipo de carrera: Maestria"
    assert valores["Exportado por"] == "coord@utn.test"
    assert libro["Cohortes"].auto_filter.ref is not None
