"""Tests unitarios del Módulo C: límites del semáforo, graduación y override manual."""
from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from src.inscripcion.domain.entities import EstadoLegajo
from src.seguimiento_graduacion.application.gestionar_graduacion import puede_graduarse
from src.seguimiento_graduacion.application.gestionar_trabajos_finales import editar_trabajo_final
from src.seguimiento_graduacion.application.recalcular_semaforos import (
    _motivo_y_dias, recalcular_semaforos, restaurar_semaforo_automatico,
)
from src.seguimiento_graduacion.domain.repo import FilaSeguimiento
from src.seguimiento_graduacion.domain.semaforo import DatosSemaforo, EstadoSemaforo, calcular_semaforo
from src.seguimiento_graduacion.domain.trabajo_final import (
    ReglaTrabajoFinalViolada, TipoTrabajoFinal, TrabajoFinal,
)

INICIO = date(2026, 4, 1)


def _datos(tipo: str, dias: int, **cambios) -> DatosSemaforo:
    base = dict(
        tipo_carrera=tipo, fecha_inscripcion=INICIO,
        seminarios_obligatorios_total=8, seminarios_aprobados=0,
        tiene_tfi_registrado=False, tiene_director_asignado=False, tiene_fecha_cpr=False,
        hoy=INICIO + timedelta(days=dias),
    )
    base.update(cambios)
    return DatosSemaforo(**base)


def _fila(legajo_id: str, semaforo: str = "VERDE") -> FilaSeguimiento:
    return FilaSeguimiento(
        legajo_id=legajo_id, numero_legajo=f"27-001-{legajo_id}", apellido="Pérez", nombre="Ana",
        carrera_nombre="Maestría", tipo_carrera="Maestria", fecha_inscripcion=INICIO,
        semaforo=semaforo, semaforo_manual=False, semaforo_desde=None,
        seminarios_obligatorios_total=8, seminarios_aprobados=0,
        tiene_tfi_registrado=False, tiene_fecha_cpr=False,
    )


class RepoSeguimientoFalso:
    """Repo en memoria para probar el caso de uso sin base de datos."""

    def __init__(self, datos: dict[str, DatosSemaforo], filas: dict[str, FilaSeguimiento]):
        self.datos = datos
        self.filas = filas
        self.manuales: set[str] = set()
        self.guardados: list[tuple[str, str]] = []
        self.limpiados: list[str] = []

    async def legajos_activos_ids(self) -> list[str]:
        return list(self.datos)

    async def datos_de_legajo(self, legajo_id: str) -> DatosSemaforo | None:
        return self.datos.get(legajo_id)

    async def obtener_fila(self, legajo_id: str) -> FilaSeguimiento | None:
        fila = self.filas.get(legajo_id)
        if fila is None:
            return None
        return replace(fila, semaforo_manual=legajo_id in self.manuales)

    async def guardar_semaforo(self, legajo_id: str, estado: str, fecha: datetime) -> bool:
        if legajo_id in self.manuales:
            return False
        fila = self.filas[legajo_id]
        if fila.semaforo == estado and fila.semaforo_desde is not None:
            return False
        self.guardados.append((legajo_id, estado))
        self.filas[legajo_id] = replace(self.filas[legajo_id], semaforo=estado, semaforo_desde=fecha)
        return True

    async def limpiar_semaforo_manual(self, legajo_id: str, fecha: datetime) -> None:
        self.manuales.discard(legajo_id)
        self.limpiados.append(legajo_id)


# ── Límites exactos de los umbrales ─────────────────────────────────────────

def test_limite_exacto_de_rojo_en_especializacion():
    # 0.75 * 730 = 547,5 días: con 547 aún no cruza, con 548 sí
    assert calcular_semaforo(_datos("Especializacion", 547, seminarios_aprobados=6)) == EstadoSemaforo.AMARILLO
    assert calcular_semaforo(_datos("Especializacion", 548, seminarios_aprobados=6)) == EstadoSemaforo.ROJO


def test_limite_exacto_de_amarillo_en_maestria():
    # 0.5 * 1095 = 547,5
    assert calcular_semaforo(_datos("Maestria", 547)) == EstadoSemaforo.VERDE
    assert calcular_semaforo(_datos("Maestria", 548)) == EstadoSemaforo.AMARILLO


def test_tipo_de_carrera_desconocido_queda_verde():
    assert calcular_semaforo(_datos("Otro", 3000)) == EstadoSemaforo.VERDE


def test_sin_fecha_de_inscripcion_queda_verde():
    datos = _datos("Doctorado", 10, fecha_inscripcion=None)
    assert calcular_semaforo(datos) == EstadoSemaforo.VERDE


def test_motivo_y_dias_restantes():
    motivo, dias = _motivo_y_dias(_datos("Doctorado", 1400))
    assert "70 %" in motivo and "CPR" in motivo
    assert dias == 1825 - 1400


# ── Graduación ──────────────────────────────────────────────────────────────

def test_puede_graduarse_solo_si_activo_con_cpr_y_sin_deudas():
    cpr = date(2026, 10, 1)
    assert puede_graduarse(EstadoLegajo.ACTIVO, cpr, 0, 2)
    assert not puede_graduarse(EstadoLegajo.COMPLETADO, cpr, 0, 2)
    assert not puede_graduarse(EstadoLegajo.ACTIVO, None, 0, 2)
    assert not puede_graduarse(EstadoLegajo.ACTIVO, cpr, 1, 2)
    assert not puede_graduarse(EstadoLegajo.ACTIVO, cpr, 0, 0)


def test_fecha_de_cpr_no_puede_ser_futura():
    with pytest.raises(ReglaTrabajoFinalViolada):
        TrabajoFinal(
            id="1", legajo_id="l", tipo="TFI", titulo="Un título válido",
            director_nombre="Ana", director_email="ana@mail.com",
            fecha_aprobacion_cpr=date.today() + timedelta(days=1),
        )


# ── Recálculo, avisos y VERDE manual ────────────────────────────────────────

async def test_recalculo_detecta_solo_los_nuevos_en_rojo_y_respeta_manual():
    datos = {
        "nuevo": _datos("Maestria", 900),
        "ya_rojo": _datos("Maestria", 900),
        "manual": _datos("Maestria", 900),
    }
    repo = RepoSeguimientoFalso(datos, {
        "nuevo": _fila("nuevo"), "ya_rojo": _fila("ya_rojo", "ROJO"), "manual": _fila("manual"),
    })
    repo.manuales.add("manual")
    repo.filas["ya_rojo"] = replace(repo.filas["ya_rojo"], semaforo_desde=datetime.now())

    resultado = await recalcular_semaforos(repo)

    assert resultado.evaluados == 3
    assert resultado.actualizados == 1  # el manual no se tocó y el ya rojo no cambió
    assert [cambio.legajo_id for cambio in resultado.nuevos_en_riesgo] == ["nuevo"]
    assert resultado.nuevos_en_riesgo[0].dias_restantes == 1095 - 900


async def test_restaurar_verde_manual_vuelve_a_calcular():
    repo = RepoSeguimientoFalso(
        {"a": _datos("Maestria", 900)}, {"a": _fila("a", "VERDE")}
    )
    repo.manuales.add("a")
    fila = await restaurar_semaforo_automatico(repo, "a")

    assert repo.limpiados == ["a"]
    assert fila.semaforo == "ROJO"
    assert not fila.semaforo_manual


async def test_editar_trabajo_final_puede_quitar_la_fecha_cpr():
    class RepoTrabajosFalso:
        def __init__(self, trabajo):
            self.trabajo = trabajo

        async def obtener_por_id(self, trabajo_id):
            return self.trabajo

        async def actualizar(self, trabajo):
            return trabajo

    trabajo = TrabajoFinal(
        id="t1", legajo_id="l1", tipo=TipoTrabajoFinal.TFI,
        titulo="Trabajo de prueba", director_nombre="Ana", director_email="ana@mail.com",
        fecha_aprobacion_cpr=date(2026, 1, 1),
    )
    repo = RepoTrabajosFalso(trabajo)
    actualizado = await editar_trabajo_final("t1", repo, limpiar_fecha_cpr=True)
    assert actualizado.fecha_aprobacion_cpr is None
