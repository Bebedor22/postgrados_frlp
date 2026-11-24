"""Repositorio Postgres de métricas (Módulo D)."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.domain.metricas import CohorteInfo, LegajoMetrica
from src.analytics.domain.repo import MetricasRepository
from src.inscripcion.infrastructure.orm_models import LegajoModel
from src.oferta_academica.infrastructure.orm_models import CarreraModel, CohorteModel


def _fecha(valor):
    return valor.date() if valor is not None else None


def _a_uuid(valor):
    import uuid

    return valor if isinstance(valor, uuid.UUID) else uuid.UUID(str(valor))


class PostgresMetricasRepository(MetricasRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def cargar_legajos(self, cohorte_id: Optional[str] = None) -> list[LegajoMetrica]:
        consulta = (
            select(
                LegajoModel.id,
                LegajoModel.cohorte_id,
                CohorteModel.nombre.label("cohorte_nombre"),
                CohorteModel.anio.label("cohorte_anio"),
                CarreraModel.nombre.label("carrera_nombre"),
                LegajoModel.tipo_carrera,
                LegajoModel.estado,
                LegajoModel.semaforo,
                LegajoModel.fecha_inscripcion,
                LegajoModel.fecha_graduacion,
            )
            .join(CohorteModel, CohorteModel.id == LegajoModel.cohorte_id)
            .outerjoin(CarreraModel, CarreraModel.id == LegajoModel.carrera_id)
        )
        if cohorte_id:
            consulta = consulta.where(LegajoModel.cohorte_id == _a_uuid(cohorte_id))

        resultado = await self._session.execute(consulta)
        return [
            LegajoMetrica(
                legajo_id=str(fila.id),
                cohorte_id=str(fila.cohorte_id),
                cohorte_nombre=fila.cohorte_nombre,
                cohorte_anio=fila.cohorte_anio,
                carrera_nombre=fila.carrera_nombre or "",
                tipo_carrera=fila.tipo_carrera,
                estado=fila.estado,
                semaforo=fila.semaforo,
                fecha_inscripcion=_fecha(fila.fecha_inscripcion),
                fecha_graduacion=_fecha(fila.fecha_graduacion),
            )
            for fila in resultado.all()
        ]

    async def listar_cohortes(self) -> list[CohorteInfo]:
        resultado = await self._session.execute(
            select(CohorteModel.id, CohorteModel.nombre, CohorteModel.anio)
            .order_by(CohorteModel.anio.desc(), CohorteModel.nombre)
        )
        return [
            CohorteInfo(id=str(fila.id), nombre=fila.nombre, anio=fila.anio)
            for fila in resultado.all()
        ]
