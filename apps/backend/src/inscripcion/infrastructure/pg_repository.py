import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.inscripcion.domain.entities import EstadoLegajo, Legajo, TipoCarrera
from src.inscripcion.domain.repo import LegajoRepository
from src.inscripcion.domain.value_objects import DNI, Email
from src.inscripcion.infrastructure.orm_models import AuditoriaLegajoModel, LegajoModel
from src.shared.exceptions import LegajoNoEncontrado


def _a_uuid(valor) -> uuid.UUID:
    """Convierte un id recibido como texto a UUID (asyncpg no acepta str en columnas UUID)."""
    return valor if isinstance(valor, uuid.UUID) else uuid.UUID(str(valor))


class PostgresLegajoRepository(LegajoRepository):
    """Implementación concreta de LegajoRepository usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def guardar(self, legajo: Legajo) -> Legajo:
        """Guardar un legajo nuevo en la base de datos."""
        legajo_model = LegajoModel(
            id=_a_uuid(legajo.id),
            numero_legajo=legajo.numero_legajo,
            cohorte_id=_a_uuid(legajo.cohorte_id),
            dni=str(legajo.dni),
            apellido=legajo.apellido,
            nombre=legajo.nombre,
            email=str(legajo.email),
            tipo_carrera=legajo.tipo_carrera.valor,
            solicita_beca=legajo.solicita_beca,
            tipo_beca=legajo.tipo_beca,
            estado=legajo.estado.value,
            fecha_inscripcion=legajo.fecha_inscripcion,
            fecha_activacion=legajo.fecha_activacion,
            semaforo=legajo.semaforo,
            semaforo_manual=legajo.semaforo_manual,
        )
        self._session.add(legajo_model)
        await self._session.flush()
        return self._modelo_a_dominio(legajo_model)

    async def obtener_por_dni(self, dni: str) -> Optional[Legajo]:
        """Obtener el primer legajo con ese DNI (o None)."""
        result = await self._session.execute(select(LegajoModel).where(LegajoModel.dni == dni))
        modelo = result.scalars().first()
        return self._modelo_a_dominio(modelo) if modelo else None

    async def obtener_por_id(self, legajo_id: str) -> Legajo:
        """Obtener un legajo por su ID. Lanza LegajoNoEncontrado si no existe."""
        modelo = await self._obtener_modelo(legajo_id)
        return self._modelo_a_dominio(modelo)

    async def listar_por_cohorte_y_estado(self, cohorte_id: str, estado: EstadoLegajo) -> list[Legajo]:
        """Listar legajos de una cohorte con un estado específico."""
        result = await self._session.execute(
            select(LegajoModel)
            .where(LegajoModel.cohorte_id == _a_uuid(cohorte_id))
            .where(LegajoModel.estado == estado.value)
        )
        return [self._modelo_a_dominio(m) for m in result.scalars().all()]

    async def listar_en_estado(self, estado: EstadoLegajo) -> list[Legajo]:
        """Listar todos los legajos en un estado dado."""
        result = await self._session.execute(select(LegajoModel).where(LegajoModel.estado == estado.value))
        return [self._modelo_a_dominio(m) for m in result.scalars().all()]

    async def actualizar_estado(
            self,
            legajo_id: str,
            nuevo_estado: EstadoLegajo,
            comentario: Optional[str] = None,
            usuario_email: Optional[str] = None,
    ) -> Legajo:
        """Actualizar el estado de un legajo y registrar el cambio en la auditoría."""
        legajo_model = await self._obtener_modelo(legajo_id)
        estado_anterior = legajo_model.estado
        legajo_model.estado = nuevo_estado.value

        self._session.add(
            AuditoriaLegajoModel(
                legajo_id=legajo_model.id,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado.value,
                comentario=comentario,
                usuario_email=usuario_email,
            )
        )
        await self._session.flush()
        return self._modelo_a_dominio(legajo_model)

    async def existe_dni_en_cohorte(self, dni: str, cohorte_id: str) -> bool:
        """Verificar si ya existe un aspirante con ese DNI en la cohorte."""
        result = await self._session.execute(
            select(LegajoModel.id)
            .where(LegajoModel.dni == dni)
            .where(LegajoModel.cohorte_id == _a_uuid(cohorte_id))
        )
        return result.first() is not None

    # ── Helpers privados ─────────────────────────────────────────────────────

    async def _obtener_modelo(self, legajo_id: str) -> LegajoModel:
        try:
            clave = _a_uuid(legajo_id)
        except ValueError:
            raise LegajoNoEncontrado(str(legajo_id))
        modelo = await self._session.get(LegajoModel, clave)
        if modelo is None:
            raise LegajoNoEncontrado(str(legajo_id))
        return modelo

    @staticmethod
    def _modelo_a_dominio(modelo: LegajoModel) -> Legajo:
        """Convertir el modelo SQLAlchemy en la entidad de dominio."""
        return Legajo(
            id=str(modelo.id),
            numero_legajo=modelo.numero_legajo,
            cohorte_id=str(modelo.cohorte_id) if modelo.cohorte_id else "",
            dni=DNI(modelo.dni),
            apellido=modelo.apellido,
            nombre=modelo.nombre,
            email=Email(modelo.email),
            tipo_carrera=TipoCarrera(modelo.tipo_carrera),
            solicita_beca=modelo.solicita_beca,
            tipo_beca=modelo.tipo_beca,
            estado=EstadoLegajo(modelo.estado),
            fecha_inscripcion=modelo.fecha_inscripcion,
            fecha_activacion=modelo.fecha_activacion,
            semaforo=modelo.semaforo,
            semaforo_manual=modelo.semaforo_manual,
        )