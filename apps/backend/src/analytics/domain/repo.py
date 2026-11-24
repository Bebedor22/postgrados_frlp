"""Interfaz de lectura de datos para las métricas del Módulo D."""
from typing import Optional

from .metricas import CohorteInfo, LegajoMetrica


class MetricasRepository:
    async def cargar_legajos(
            self, cohorte_id: Optional[str] = None, tipo_carrera: Optional[str] = None
    ) -> list[LegajoMetrica]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def listar_cohortes(self) -> list[CohorteInfo]:
        raise NotImplementedError("Implementar en pg_repository.py")
