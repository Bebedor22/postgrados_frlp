import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.oferta_academica.domain.entities import Carrera, Cohorte
from src.oferta_academica.infrastructure.orm_models import CarreraModel, CohorteModel


class PostgresCarreraRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def listar(self, solo_activas: bool = True) -> list[Carrera]:
        consulta = select(CarreraModel).order_by(CarreraModel.tipo, CarreraModel.nombre)
        if solo_activas:
            consulta = consulta.where(CarreraModel.activa.is_(True))
        result = await self._session.execute(consulta)
        return [self._a_dominio(m) for m in result.scalars().all()]

    async def obtener_por_nombre(self, nombre: str) -> Optional[Carrera]:
        result = await self._session.execute(select(CarreraModel).where(CarreraModel.nombre == nombre))
        modelo = result.scalar_one_or_none()
        return self._a_dominio(modelo) if modelo else None

    async def guardar(self, carrera: Carrera) -> Carrera:
        self._session.add(
            CarreraModel(
                id=uuid.UUID(carrera.id),
                nombre=carrera.nombre,
                tipo=carrera.tipo,
                duracion_anios=carrera.duracion_anios,
                activa=carrera.activa,
            )
        )
        await self._session.flush()
        return carrera

    @staticmethod
    def _a_dominio(m: CarreraModel) -> Carrera:
        return Carrera(id=str(m.id), nombre=m.nombre, tipo=m.tipo, duracion_anios=m.duracion_anios, activa=m.activa)


class PostgresCohorteRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def listar(self, solo_abiertas: bool = False) -> list[Cohorte]:
        consulta = select(CohorteModel).order_by(CohorteModel.anio.desc())
        if solo_abiertas:
            consulta = consulta.where(CohorteModel.abierta.is_(True))
        result = await self._session.execute(consulta)
        return [self._a_dominio(m) for m in result.scalars().all()]

    async def obtener_por_id(self, cohorte_id: str) -> Optional[Cohorte]:
        try:
            clave = uuid.UUID(str(cohorte_id))
        except ValueError:
            return None
        modelo = await self._session.get(CohorteModel, clave)
        return self._a_dominio(modelo) if modelo else None

    async def obtener_por_nombre(self, nombre: str) -> Optional[Cohorte]:
        result = await self._session.execute(select(CohorteModel).where(CohorteModel.nombre == nombre))
        modelo = result.scalar_one_or_none()
        return self._a_dominio(modelo) if modelo else None

    async def guardar(self, cohorte: Cohorte) -> Cohorte:
        self._session.add(
            CohorteModel(
                id=uuid.UUID(cohorte.id),
                anio=cohorte.anio,
                nombre=cohorte.nombre,
                abierta=cohorte.inscripcion_abierta,
                fecha_inicio=cohorte.fecha_inicio,
            )
        )
        await self._session.flush()
        return cohorte

    async def actualizar(self, cohorte: Cohorte) -> Cohorte:
        modelo = await self._session.get(CohorteModel, uuid.UUID(cohorte.id))
        modelo.abierta = cohorte.inscripcion_abierta
        await self._session.flush()
        return cohorte

    @staticmethod
    def _a_dominio(m: CohorteModel) -> Cohorte:
        return Cohorte(
            id=str(m.id), anio=m.anio, nombre=m.nombre, inscripcion_abierta=m.abierta, fecha_inicio=m.fecha_inicio
        )