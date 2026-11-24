"""Esquemas Pydantic del dashboard (Módulo D)."""
from typing import Optional

from pydantic import BaseModel


class MetricasCohorteResponse(BaseModel):
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


class DashboardResponse(BaseModel):
    total_inscriptos: int
    activos: int
    graduados: int
    bajas: int
    en_riesgo: int
    retencion_pct: float
    desgranamiento_pct: float
    tiempo_promedio_graduacion_dias: Optional[float] = None
    por_estado: dict[str, int]
    por_tipo_carrera: dict[str, int]
    cohortes: list[MetricasCohorteResponse]
