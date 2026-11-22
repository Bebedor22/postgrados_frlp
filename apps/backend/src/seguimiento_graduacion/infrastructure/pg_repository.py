"""Repositorios Postgres del Módulo C."""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.carga_academica.domain.entities import EstadoSeminario
from src.carga_academica.infrastructure.orm_models import InscripcionSeminarioModel, SeminarioModel
from src.inscripcion.domain.entities import EstadoLegajo
from src.inscripcion.infrastructure.orm_models import LegajoModel
from src.oferta_academica.infrastructure.orm_models import CarreraModel
from src.seguimiento_graduacion.domain.repo import FilaSeguimiento, SeguimientoRepository, TrabajoFinalRepository
from src.seguimiento_graduacion.domain.semaforo import DatosSemaforo
from src.seguimiento_graduacion.domain.trabajo_final import TipoTrabajoFinal, TrabajoFinal
from src.seguimiento_graduacion.infrastructure.orm_models import TrabajoFinalModel


def _a_uuid(valor) -> uuid.UUID:
    return valor if isinstance(valor, uuid.UUID) else uuid.UUID(str(valor))


def _fecha(valor: Optional[datetime]) -> Optional[date]:
    return valor.date() if valor is not None else None


class PostgresTrabajoFinalRepository(TrabajoFinalRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def crear(self, trabajo: TrabajoFinal) -> TrabajoFinal:
        modelo = TrabajoFinalModel(
            id=uuid.uuid4(),
            legajo_id=_a_uuid(trabajo.legajo_id),
            tipo=trabajo.tipo.value,
            titulo=trabajo.titulo,
            director_nombre=trabajo.director_nombre,
            director_email=trabajo.director_email,
            codirector_nombre=trabajo.codirector_nombre,
            fecha_aprobacion_cpr=trabajo.fecha_aprobacion_cpr,
            numero_resolucion=trabajo.numero_resolucion,
        )
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_por_id(self, trabajo_id: str) -> Optional[TrabajoFinal]:
        try:
            modelo = await self._session.get(TrabajoFinalModel, _a_uuid(trabajo_id))
        except ValueError:
            return None
        return self._a_dominio(modelo) if modelo else None

    async def obtener_por_legajo(self, legajo_id: str) -> Optional[TrabajoFinal]:
        try:
            clave = _a_uuid(legajo_id)
        except ValueError:
            return None
        modelo = await self._session.scalar(
            select(TrabajoFinalModel).where(TrabajoFinalModel.legajo_id == clave)
        )
        return self._a_dominio(modelo) if modelo else None

    async def actualizar(self, trabajo: TrabajoFinal) -> TrabajoFinal:
        modelo = await self._session.get(TrabajoFinalModel, _a_uuid(trabajo.id))
        if modelo is None:
            raise LookupError(f"No existe el trabajo final {trabajo.id}")
        modelo.tipo = trabajo.tipo.value
        modelo.titulo = trabajo.titulo
        modelo.director_nombre = trabajo.director_nombre
        modelo.director_email = trabajo.director_email
        modelo.codirector_nombre = trabajo.codirector_nombre
        modelo.fecha_aprobacion_cpr = trabajo.fecha_aprobacion_cpr
        modelo.numero_resolucion = trabajo.numero_resolucion
        modelo.updated_at = datetime.now()
        await self._session.flush()
        return self._a_dominio(modelo)

    @staticmethod
    def _a_dominio(m: TrabajoFinalModel) -> TrabajoFinal:
        return TrabajoFinal(
            id=str(m.id),
            legajo_id=str(m.legajo_id),
            tipo=TipoTrabajoFinal(m.tipo),
            titulo=m.titulo,
            director_nombre=m.director_nombre,
            director_email=m.director_email,
            codirector_nombre=m.codirector_nombre,
            fecha_aprobacion_cpr=m.fecha_aprobacion_cpr,
            numero_resolucion=m.numero_resolucion,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class PostgresSeguimientoRepository(SeguimientoRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def _legajo(self, legajo_id: str) -> Optional[LegajoModel]:
        try:
            return await self._session.get(LegajoModel, _a_uuid(legajo_id))
        except ValueError:
            return None

    async def _conteos(self, legajo: LegajoModel) -> tuple[int, int]:
        total = await self._session.scalar(
            select(func.count())
            .select_from(SeminarioModel)
            .where(SeminarioModel.carrera_id == legajo.carrera_id)
            .where(SeminarioModel.es_obligatorio.is_(True))
        )
        aprobados = await self._session.scalar(
            select(func.count())
            .select_from(InscripcionSeminarioModel)
            .join(SeminarioModel, SeminarioModel.id == InscripcionSeminarioModel.seminario_id)
            .where(InscripcionSeminarioModel.legajo_id == legajo.id)
            .where(SeminarioModel.es_obligatorio.is_(True))
            .where(InscripcionSeminarioModel.estado == EstadoSeminario.APROBADO.value)
        )
        return total or 0, aprobados or 0

    async def _trabajo(self, legajo: LegajoModel) -> Optional[TrabajoFinalModel]:
        return await self._session.scalar(
            select(TrabajoFinalModel).where(TrabajoFinalModel.legajo_id == legajo.id)
        )

    @staticmethod
    def _fecha_referencia(legajo: LegajoModel) -> Optional[date]:
        return _fecha(legajo.fecha_activacion or legajo.fecha_inscripcion)

    async def datos_de_legajo(self, legajo_id: str) -> Optional[DatosSemaforo]:
        legajo = await self._legajo(legajo_id)
        if legajo is None:
            return None
        total, aprobados = await self._conteos(legajo)
        trabajo = await self._trabajo(legajo)
        return DatosSemaforo(
            tipo_carrera=legajo.tipo_carrera,
            fecha_inscripcion=self._fecha_referencia(legajo),
            seminarios_obligatorios_total=total,
            seminarios_aprobados=aprobados,
            tiene_tfi_registrado=trabajo is not None,
            tiene_director_asignado=bool(trabajo and trabajo.director_nombre),
            tiene_fecha_cpr=bool(trabajo and trabajo.fecha_aprobacion_cpr),
        )

    async def legajos_activos_ids(self) -> list[str]:
        resultado = await self._session.execute(
            select(LegajoModel.id).where(LegajoModel.estado == EstadoLegajo.ACTIVO.value)
        )
        return [str(fila[0]) for fila in resultado.all()]

    async def guardar_semaforo(self, legajo_id: str, estado: str, fecha: datetime) -> bool:
        legajo = await self._legajo(legajo_id)
        if legajo is None:
            return False
        if legajo.semaforo_manual:
            return False
        if legajo.semaforo == estado and legajo.semaforo_desde is not None:
            return False
        legajo.semaforo = estado
        legajo.semaforo_desde = fecha
        legajo.updated_at = fecha
        await self._session.flush()
        return True

    async def marcar_verde_manual(self, legajo_id: str, fecha: datetime) -> None:
        legajo = await self._legajo(legajo_id)
        if legajo is None:
            return
        legajo.semaforo = "VERDE"
        legajo.semaforo_manual = True
        legajo.semaforo_desde = fecha
        legajo.updated_at = fecha
        await self._session.flush()

    async def limpiar_semaforo_manual(self, legajo_id: str, fecha: datetime) -> None:
        legajo = await self._legajo(legajo_id)
        if legajo is None:
            return
        legajo.semaforo_manual = False
        legajo.semaforo_desde = None
        legajo.updated_at = fecha
        await self._session.flush()

    async def _fila(self, legajo: LegajoModel) -> FilaSeguimiento:
        total, aprobados = await self._conteos(legajo)
        trabajo = await self._trabajo(legajo)
        carrera_nombre = await self._session.scalar(
            select(CarreraModel.nombre).where(CarreraModel.id == legajo.carrera_id)
        ) if legajo.carrera_id else None
        return FilaSeguimiento(
            legajo_id=str(legajo.id),
            numero_legajo=legajo.numero_legajo,
            apellido=legajo.apellido,
            nombre=legajo.nombre,
            carrera_nombre=carrera_nombre or "",
            tipo_carrera=legajo.tipo_carrera,
            fecha_inscripcion=self._fecha_referencia(legajo),
            semaforo=legajo.semaforo,
            semaforo_manual=legajo.semaforo_manual,
            semaforo_desde=legajo.semaforo_desde,
            seminarios_obligatorios_total=total,
            seminarios_aprobados=aprobados,
            tiene_tfi_registrado=trabajo is not None,
            tiene_fecha_cpr=bool(trabajo and trabajo.fecha_aprobacion_cpr),
        )

    async def obtener_fila(self, legajo_id: str) -> Optional[FilaSeguimiento]:
        legajo = await self._legajo(legajo_id)
        return await self._fila(legajo) if legajo else None

    async def listar_en_riesgo(self) -> list[FilaSeguimiento]:
        resultado = await self._session.execute(
            select(LegajoModel)
            .where(LegajoModel.estado == EstadoLegajo.ACTIVO.value)
            .where(LegajoModel.semaforo == "ROJO")
        )
        return [await self._fila(legajo) for legajo in resultado.scalars().all()]

    async def listar_activos(self) -> list[FilaSeguimiento]:
        resultado = await self._session.execute(
            select(LegajoModel).where(LegajoModel.estado == EstadoLegajo.ACTIVO.value)
        )
        return [await self._fila(legajo) for legajo in resultado.scalars().all()]
