"""Recálculo del semáforo (RF-GRAD-002, BR-008, US-C-004)."""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from ..domain.repo import FilaSeguimiento, SeguimientoRepository
from ..domain.semaforo import DURACION_DIAS, DatosSemaforo, calcular_semaforo


class LegajoSinDatosAcademicos(LookupError):
    pass


@dataclass
class CambioSemaforo:
    """Un legajo que acaba de pasar a ROJO (para avisar a la coordinación)."""

    legajo_id: str
    estado_anterior: str
    estado_nuevo: str
    motivo: str
    dias_restantes: int


@dataclass
class ResultadoRecalculo:
    evaluados: int
    actualizados: int
    nuevos_en_riesgo: list[CambioSemaforo] = field(default_factory=list)


def _motivo_y_dias(datos: DatosSemaforo) -> tuple[str, int]:
    """Texto del aviso y días que quedan hasta el plazo normativo (US-C-004)."""
    if datos.fecha_inscripcion is None:
        return "sin fecha de inscripción", 0
    dias = ((datos.hoy or date.today()) - datos.fecha_inscripcion).days
    duracion = DURACION_DIAS.get(datos.tipo_carrera, 0)
    restantes = max(duracion - dias, 0)
    motivos = {
        "Especializacion": "superó el 75 % del plazo y adeuda seminarios obligatorios",
        "Maestria": "superó el 80 % del plazo y adeuda seminarios obligatorios",
        "Doctorado": "superó el 70 % del plazo sin fecha de aprobación CPR",
    }
    return motivos.get(datos.tipo_carrera, "cruzó el umbral de riesgo de su carrera"), restantes


async def recalcular_legajo(
        repo: SeguimientoRepository, legajo_id: str, hoy: Optional[date] = None
) -> FilaSeguimiento:
    datos = await repo.datos_de_legajo(legajo_id)
    if datos is None:
        raise LegajoSinDatosAcademicos(f"No existe el legajo {legajo_id}")
    if hoy is not None:
        datos.hoy = hoy
    estado = calcular_semaforo(datos)
    await repo.guardar_semaforo(legajo_id, estado.value, datetime.now())
    fila = await repo.obtener_fila(legajo_id)
    if fila is None:
        raise LegajoSinDatosAcademicos(f"No existe el legajo {legajo_id}")
    return fila


async def recalcular_semaforos(
        repo: SeguimientoRepository, hoy: Optional[date] = None
) -> ResultadoRecalculo:
    """Job diario: recalcula los legajos ACTIVO y detecta los que recién pasan a ROJO.

    Respeta el VERDE manual: `guardar_semaforo` devuelve False en ese caso, así que
    esos legajos nunca generan avisos de riesgo.
    """
    ids = await repo.legajos_activos_ids()
    actualizados = 0
    nuevos_en_riesgo: list[CambioSemaforo] = []
    for legajo_id in ids:
        fila_antes = await repo.obtener_fila(legajo_id)
        datos = await repo.datos_de_legajo(legajo_id)
        if datos is None:
            continue
        if hoy is not None:
            datos.hoy = hoy
        estado = calcular_semaforo(datos).value
        if await repo.guardar_semaforo(legajo_id, estado, datetime.now()):
            actualizados += 1
            anterior = fila_antes.semaforo if fila_antes is not None else "VERDE"
            if estado == "ROJO" and anterior != "ROJO":
                motivo, dias = _motivo_y_dias(datos)
                nuevos_en_riesgo.append(CambioSemaforo(
                    legajo_id=legajo_id, estado_anterior=anterior, estado_nuevo=estado,
                    motivo=motivo, dias_restantes=dias,
                ))
    return ResultadoRecalculo(
        evaluados=len(ids), actualizados=actualizados, nuevos_en_riesgo=nuevos_en_riesgo,
    )


async def marcar_verde_manual(
        repo: SeguimientoRepository, legajo_id: str
) -> FilaSeguimiento:
    """BR-008: el coordinador fija VERDE; el recálculo automático no lo pisa."""
    if await repo.datos_de_legajo(legajo_id) is None:
        raise LegajoSinDatosAcademicos(f"No existe el legajo {legajo_id}")
    await repo.marcar_verde_manual(legajo_id, datetime.now())
    fila = await repo.obtener_fila(legajo_id)
    if fila is None:
        raise LegajoSinDatosAcademicos(f"No existe el legajo {legajo_id}")
    return fila


async def restaurar_semaforo_automatico(
        repo: SeguimientoRepository, legajo_id: str
) -> FilaSeguimiento:
    """Vuelve a dejar que el algoritmo calcule el color del legajo (BR-008)."""
    if await repo.datos_de_legajo(legajo_id) is None:
        raise LegajoSinDatosAcademicos(f"No existe el legajo {legajo_id}")
    await repo.limpiar_semaforo_manual(legajo_id, datetime.now())
    return await recalcular_legajo(repo, legajo_id)


async def legajos_en_riesgo(
        repo: SeguimientoRepository, hoy: Optional[date] = None
) -> list[FilaSeguimiento]:
    filas = await repo.listar_en_riesgo()
    return sorted(filas, key=lambda fila: fila.dias_en_riesgo(hoy), reverse=True)
