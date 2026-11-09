import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.inscripcion.domain.entities import CambioDeEstado, EstadoLegajo, Legajo, TipoCarrera
from src.inscripcion.domain.formulario import FormularioInscripcion
from src.inscripcion.domain.repo import FiltrosLegajos, LegajoRepository
from src.inscripcion.domain.value_objects import Email, crear_documento
from src.inscripcion.infrastructure.orm_models import AuditoriaLegajoModel, DatosAspiranteModel, LegajoModel
from src.shared.exceptions import LegajoNoEncontrado

# Estados en los que la inscripción ya no cuenta para el máximo de carreras (BR-001)
ESTADOS_NO_VIGENTES = (EstadoLegajo.RECHAZADO.value, EstadoLegajo.BAJA.value, EstadoLegajo.VENCIDO.value)

# Campos del formulario que se guardan en la tabla legajos (el resto va a datos_aspirante)
CAMPOS_EN_LEGAJO = {"nombre", "apellido", "email", "solicita_beca", "tipo_beca"}
CAMPOS_FIJOS = {"tipo_documento", "numero_documento"}


def _a_uuid(valor) -> uuid.UUID:
    """Convierte un id recibido como texto a UUID (asyncpg no acepta str en columnas UUID)."""
    return valor if isinstance(valor, uuid.UUID) else uuid.UUID(str(valor))


class PostgresLegajoRepository(LegajoRepository):
    """Implementación concreta de LegajoRepository usando SQLAlchemy async."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def guardar(self, legajo: Legajo) -> Legajo:
        """Guardar un legajo nuevo en la base de datos."""
        legajo_model = self._dominio_a_modelo(legajo)
        self._session.add(legajo_model)
        await self._session.flush()
        return self._modelo_a_dominio(legajo_model)

    async def obtener_por_dni(self, dni: str) -> Optional[Legajo]:
        """Obtener el primer legajo con ese documento (o None)."""
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
        """Verificar si ya existe un aspirante con ese documento en la cohorte."""
        result = await self._session.execute(
            select(LegajoModel.id)
            .where(LegajoModel.dni == dni)
            .where(LegajoModel.cohorte_id == _a_uuid(cohorte_id))
        )
        return result.first() is not None

    # ── Inscripción por pasos ────────────────────────────────────────────────

    async def crear_inscripcion(
            self, legajo: Legajo, formulario: FormularioInscripcion, token_hash: str
    ) -> Legajo:
        modelo = self._dominio_a_modelo(legajo)
        modelo.token_seguimiento_hash = token_hash
        self._session.add(modelo)
        self._session.add(DatosAspiranteModel(legajo_id=modelo.id))
        self._session.add(
            AuditoriaLegajoModel(
                legajo_id=modelo.id,
                estado_anterior=None,
                estado_nuevo=EstadoLegajo.BORRADOR.value,
                comentario="Inscripción iniciada",
                usuario_email=str(legajo.email),
            )
        )
        await self._session.flush()
        return legajo

    async def obtener_por_token(self, token_hash: str) -> Optional[Legajo]:
        result = await self._session.execute(
            select(LegajoModel).where(LegajoModel.token_seguimiento_hash == token_hash)
        )
        modelo = result.scalar_one_or_none()
        return self._modelo_a_dominio(modelo) if modelo else None

    async def obtener_formulario(self, legajo_id: str) -> FormularioInscripcion:
        legajo = await self._obtener_modelo(legajo_id)
        datos = await self._session.get(DatosAspiranteModel, legajo.id)
        formulario = FormularioInscripcion(
            nombre=legajo.nombre,
            apellido=legajo.apellido,
            tipo_documento=legajo.tipo_documento,
            numero_documento=legajo.dni,
            email=legajo.email,
            solicita_beca=legajo.solicita_beca,
            tipo_beca=legajo.tipo_beca,
        )
        if datos is not None:
            for campo in self._campos_de_datos(formulario):
                setattr(formulario, campo, getattr(datos, campo))
        return formulario

    async def guardar_formulario(self, legajo_id: str, formulario: FormularioInscripcion) -> None:
        legajo = await self._obtener_modelo(legajo_id)
        for campo in CAMPOS_EN_LEGAJO:
            setattr(legajo, campo, getattr(formulario, campo))
        datos = await self._session.get(DatosAspiranteModel, legajo.id)
        if datos is None:
            datos = DatosAspiranteModel(legajo_id=legajo.id)
            self._session.add(datos)
        for campo in self._campos_de_datos(formulario):
            setattr(datos, campo, getattr(formulario, campo))
        await self._session.flush()

    async def registrar_confirmacion(self, legajo_id: str, fecha: datetime) -> None:
        legajo = await self._obtener_modelo(legajo_id)
        legajo.fecha_inscripcion = fecha
        await self._session.flush()

    async def contar_inscripciones_vigentes(self, numero_documento: str, cohorte_id: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(LegajoModel)
            .where(LegajoModel.dni == numero_documento)
            .where(LegajoModel.cohorte_id == _a_uuid(cohorte_id))
            .where(LegajoModel.estado.not_in(ESTADOS_NO_VIGENTES))
        )
        return result.scalar_one()

    async def existe_inscripcion(self, numero_documento: str, cohorte_id: str, carrera_id: str) -> bool:
        result = await self._session.execute(
            select(LegajoModel.id)
            .where(LegajoModel.dni == numero_documento)
            .where(LegajoModel.cohorte_id == _a_uuid(cohorte_id))
            .where(LegajoModel.carrera_id == _a_uuid(carrera_id))
        )
        return result.first() is not None

    async def historial(self, legajo_id: str) -> list[CambioDeEstado]:
        result = await self._session.execute(
            select(AuditoriaLegajoModel)
            .where(AuditoriaLegajoModel.legajo_id == _a_uuid(legajo_id))
            .order_by(AuditoriaLegajoModel.created_at)
        )
        return [
            CambioDeEstado(
                estado_anterior=a.estado_anterior,
                estado_nuevo=a.estado_nuevo,
                comentario=a.comentario,
                fecha=a.created_at,
            )
            for a in result.scalars().all()
        ]

    # ── Bandeja y workflow del coordinador ───────────────────────────────────

    async def buscar(self, filtros: FiltrosLegajos) -> tuple[list[Legajo], int]:
        condiciones = []
        if filtros.cohorte_id:
            condiciones.append(LegajoModel.cohorte_id == _a_uuid(filtros.cohorte_id))
        if filtros.carrera_id:
            condiciones.append(LegajoModel.carrera_id == _a_uuid(filtros.carrera_id))
        if filtros.estado:
            condiciones.append(LegajoModel.estado == filtros.estado.value)
        if filtros.texto:
            patron = f"%{filtros.texto.strip()}%"
            condiciones.append(
                or_(
                    LegajoModel.apellido.ilike(patron),
                    LegajoModel.nombre.ilike(patron),
                    LegajoModel.dni.ilike(patron),
                    LegajoModel.email.ilike(patron),
                    LegajoModel.numero_legajo.ilike(patron),
                )
            )

        total = (
            await self._session.execute(select(func.count()).select_from(LegajoModel).where(*condiciones))
        ).scalar_one()
        result = await self._session.execute(
            select(LegajoModel)
            .where(*condiciones)
            .order_by(LegajoModel.apellido, LegajoModel.nombre)
            .offset((filtros.pagina - 1) * filtros.por_pagina)
            .limit(filtros.por_pagina)
        )
        return [self._modelo_a_dominio(m) for m in result.scalars().all()], total

    async def contar_por_estado(self, cohorte_id: Optional[str] = None) -> dict[str, int]:
        consulta = select(LegajoModel.estado, func.count()).group_by(LegajoModel.estado)
        if cohorte_id:
            consulta = consulta.where(LegajoModel.cohorte_id == _a_uuid(cohorte_id))
        result = await self._session.execute(consulta)
        return {estado: cantidad for estado, cantidad in result.all()}

    async def siguiente_secuencial(self, prefijo: str) -> int:
        result = await self._session.execute(
            select(LegajoModel.numero_legajo).where(LegajoModel.numero_legajo.like(f"{prefijo}%"))
        )
        usados = [int(n[len(prefijo):]) for n in result.scalars().all() if n[len(prefijo):].isdigit()]
        return max(usados, default=0) + 1

    async def asignar_numero(self, legajo_id: str, numero_legajo: str) -> None:
        legajo = await self._obtener_modelo(legajo_id)
        legajo.numero_legajo = numero_legajo
        await self._session.flush()

    async def registrar_activacion(self, legajo_id: str, fecha: datetime) -> None:
        legajo = await self._obtener_modelo(legajo_id)
        legajo.fecha_activacion = fecha
        await self._session.flush()

    async def fecha_de_estado(self, legajo_id: str, estado: EstadoLegajo) -> Optional[datetime]:
        result = await self._session.execute(
            select(func.max(AuditoriaLegajoModel.created_at))
            .where(AuditoriaLegajoModel.legajo_id == _a_uuid(legajo_id))
            .where(AuditoriaLegajoModel.estado_nuevo == estado.value)
        )
        return result.scalar_one()

    async def listar_en_estado_desde_antes_de(self, estado: EstadoLegajo, limite: datetime) -> list[Legajo]:
        ingreso = (
            select(AuditoriaLegajoModel.legajo_id, func.max(AuditoriaLegajoModel.created_at).label("fecha"))
            .where(AuditoriaLegajoModel.estado_nuevo == estado.value)
            .group_by(AuditoriaLegajoModel.legajo_id)
            .subquery()
        )
        result = await self._session.execute(
            select(LegajoModel)
            .join(ingreso, ingreso.c.legajo_id == LegajoModel.id)
            .where(LegajoModel.estado == estado.value)
            .where(ingreso.c.fecha < limite)
        )
        return [self._modelo_a_dominio(m) for m in result.scalars().all()]

    # ── Helpers privados ─────────────────────────────────────────────────────

    @staticmethod
    def _campos_de_datos(formulario: FormularioInscripcion) -> list[str]:
        """Campos del formulario que viven en la tabla datos_aspirante."""
        return [c for c in vars(formulario) if c not in CAMPOS_EN_LEGAJO | CAMPOS_FIJOS]

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
    def _dominio_a_modelo(legajo: Legajo) -> LegajoModel:
        return LegajoModel(
            id=_a_uuid(legajo.id),
            numero_legajo=legajo.numero_legajo,
            cohorte_id=_a_uuid(legajo.cohorte_id),
            carrera_id=_a_uuid(legajo.carrera_id) if legajo.carrera_id else None,
            tipo_documento=legajo.tipo_documento,
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

    @staticmethod
    def _modelo_a_dominio(modelo: LegajoModel) -> Legajo:
        """Convertir el modelo SQLAlchemy en la entidad de dominio."""
        return Legajo(
            id=str(modelo.id),
            numero_legajo=modelo.numero_legajo,
            cohorte_id=str(modelo.cohorte_id) if modelo.cohorte_id else "",
            carrera_id=str(modelo.carrera_id) if modelo.carrera_id else None,
            tipo_documento=modelo.tipo_documento or "DNI",
            dni=crear_documento(modelo.tipo_documento or "DNI", modelo.dni),
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