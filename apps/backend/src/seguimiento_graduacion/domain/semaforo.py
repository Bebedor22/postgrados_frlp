"""Semáforo de riesgo académico (RF-GRAD-002).

Función pura, sin SQLAlchemy ni FastAPI: se puede testear en milisegundos.
"""
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class EstadoSemaforo(Enum):
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    ROJO = "ROJO"


DURACION_DIAS = {
    "Especializacion": 730,
    "Maestria": 1095,
    "Doctorado": 1825,
}


@dataclass
class DatosSemaforo:
    tipo_carrera: str
    fecha_inscripcion: Optional[date]
    seminarios_obligatorios_total: int
    seminarios_aprobados: int
    tiene_tfi_registrado: bool
    tiene_director_asignado: bool
    tiene_fecha_cpr: bool
    hoy: Optional[date] = None


def calcular_semaforo(datos: DatosSemaforo) -> EstadoSemaforo:
    """Reglas exactas de ARQUITECTURA.md §10 / RF-GRAD-002."""
    if datos.fecha_inscripcion is None:
        return EstadoSemaforo.VERDE

    duracion = DURACION_DIAS.get(datos.tipo_carrera)
    if duracion is None:
        return EstadoSemaforo.VERDE

    hoy = datos.hoy or date.today()
    pct_tiempo = (hoy - datos.fecha_inscripcion).days / duracion

    if datos.tipo_carrera == "Especializacion":
        if pct_tiempo > 0.75 and datos.seminarios_aprobados < datos.seminarios_obligatorios_total:
            return EstadoSemaforo.ROJO
        if pct_tiempo > 0.50 and not datos.tiene_tfi_registrado:
            return EstadoSemaforo.AMARILLO

    elif datos.tipo_carrera == "Maestria":
        if pct_tiempo > 0.80 and datos.seminarios_aprobados < datos.seminarios_obligatorios_total:
            return EstadoSemaforo.ROJO
        if pct_tiempo > 0.50 and not datos.tiene_director_asignado:
            return EstadoSemaforo.AMARILLO

    elif datos.tipo_carrera == "Doctorado":
        if pct_tiempo > 0.70 and not datos.tiene_fecha_cpr:
            return EstadoSemaforo.ROJO
        if pct_tiempo > 0.40 and not datos.tiene_director_asignado:
            return EstadoSemaforo.AMARILLO

    return EstadoSemaforo.VERDE
