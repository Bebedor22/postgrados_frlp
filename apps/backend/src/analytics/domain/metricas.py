"""Métricas del dashboard (RF-REP-001).

Funciones puras: reciben filas del repositorio y devuelven los números del
dashboard. Se testean sin base de datos.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

ESTADOS_BAJA = {"BAJA", "VENCIDO", "RECHAZADO"}


@dataclass
class LegajoMetrica:
    legajo_id: str
    cohorte_id: str
    cohorte_nombre: str
    cohorte_anio: int
    carrera_nombre: str
    tipo_carrera: str
    estado: str
    semaforo: str
    fecha_inscripcion: Optional[date] = None
    fecha_graduacion: Optional[date] = None


@dataclass
class CohorteInfo:
    id: str
    nombre: str
    anio: int


@dataclass
class MetricasCohorte:
    cohorte_id: str
    cohorte_nombre: str
    cohorte_anio: int
    inscriptos: int
    activos: int
    graduados: int
    bajas: int
    en_riesgo: int
    retencion_pct: float
    desgranamiento_pct: float
    tiempo_promedio_graduacion_dias: Optional[float] = None


@dataclass
class MetricasDashboard:
    total_inscriptos: int
    activos: int
    graduados: int
    bajas: int
    en_riesgo: int
    retencion_pct: float
    desgranamiento_pct: float
    tiempo_promedio_graduacion_dias: Optional[float]
    por_estado: dict[str, int] = field(default_factory=dict)
    por_tipo_carrera: dict[str, int] = field(default_factory=dict)
    cohortes: list[MetricasCohorte] = field(default_factory=list)


def _pct(numerador: int, denominador: int) -> float:
    return round(numerador * 100 / denominador, 1) if denominador else 0.0


def _promedio_dias_graduacion(legajos: list[LegajoMetrica]) -> Optional[float]:
    dias = [
        (legajo.fecha_graduacion - legajo.fecha_inscripcion).days
        for legajo in legajos
        if legajo.estado == "GRADUADO" and legajo.fecha_graduacion and legajo.fecha_inscripcion
    ]
    return round(sum(dias) / len(dias), 1) if dias else None


def _conteos(legajos: list[LegajoMetrica]) -> dict[str, int]:
    activos = sum(1 for l in legajos if l.estado == "ACTIVO")
    graduados = sum(1 for l in legajos if l.estado == "GRADUADO")
    bajas = sum(1 for l in legajos if l.estado in ESTADOS_BAJA)
    matriculados = activos + graduados + bajas
    en_riesgo = sum(1 for l in legajos if l.estado == "ACTIVO" and l.semaforo == "ROJO")
    return {
        "inscriptos": len(legajos),
        "activos": activos,
        "graduados": graduados,
        "bajas": bajas,
        "matriculados": matriculados,
        "en_riesgo": en_riesgo,
    }


def metricas_de_cohorte(cohorte: CohorteInfo, legajos: list[LegajoMetrica]) -> MetricasCohorte:
    conteos = _conteos(legajos)
    return MetricasCohorte(
        cohorte_id=cohorte.id,
        cohorte_nombre=cohorte.nombre,
        cohorte_anio=cohorte.anio,
        inscriptos=conteos["inscriptos"],
        activos=conteos["activos"],
        graduados=conteos["graduados"],
        bajas=conteos["bajas"],
        en_riesgo=conteos["en_riesgo"],
        retencion_pct=_pct(conteos["activos"] + conteos["graduados"], conteos["matriculados"]),
        desgranamiento_pct=_pct(conteos["bajas"], conteos["matriculados"]),
        tiempo_promedio_graduacion_dias=_promedio_dias_graduacion(legajos),
    )


def calcular_dashboard(
        legajos: list[LegajoMetrica], cohortes: list[CohorteInfo]
) -> MetricasDashboard:
    """Métricas globales + una fila por cohorte (incluidas las que aún no tienen inscriptos)."""
    conteos = _conteos(legajos)
    por_estado: dict[str, int] = {}
    por_tipo: dict[str, int] = {}
    for legajo in legajos:
        por_estado[legajo.estado] = por_estado.get(legajo.estado, 0) + 1
        por_tipo[legajo.tipo_carrera] = por_tipo.get(legajo.tipo_carrera, 0) + 1

    por_cohorte: dict[str, list[LegajoMetrica]] = {}
    for legajo in legajos:
        por_cohorte.setdefault(legajo.cohorte_id, []).append(legajo)

    return MetricasDashboard(
        total_inscriptos=conteos["inscriptos"],
        activos=conteos["activos"],
        graduados=conteos["graduados"],
        bajas=conteos["bajas"],
        en_riesgo=conteos["en_riesgo"],
        retencion_pct=_pct(conteos["activos"] + conteos["graduados"], conteos["matriculados"]),
        desgranamiento_pct=_pct(conteos["bajas"], conteos["matriculados"]),
        tiempo_promedio_graduacion_dias=_promedio_dias_graduacion(legajos),
        por_estado=por_estado,
        por_tipo_carrera=por_tipo,
        cohortes=[
            metricas_de_cohorte(cohorte, por_cohorte.get(cohorte.id, []))
            for cohorte in cohortes
        ],
    )
