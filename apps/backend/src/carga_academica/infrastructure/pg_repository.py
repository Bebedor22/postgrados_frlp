"""Repositorio Postgres del Módulo B mínimo."""
import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.carga_academica.domain.entities import (
    CursadaDeLegajo,
    EstadoSeminario,
    EstudianteEnSeminario,
    InscripcionSeminario,
    ProgresoSeminarios,
    Seminario,
    validar_nota,
)
from src.carga_academica.domain.repo import InscripcionSeminarioNoEncontrada, SeminarioRepository
from src.carga_academica.infrastructure.orm_models import InscripcionSeminarioModel, SeminarioModel
from src.inscripcion.infrastructure.orm_models import LegajoModel


def _a_uuid(valor) -> uuid.UUID:
    return valor if isinstance(valor, uuid.UUID) else uuid.UUID(str(valor))


class PostgresSeminarioRepository(SeminarioRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def crear_seminario(self, seminario: Seminario) -> Seminario:
        modelo = SeminarioModel(
            id=_a_uuid(seminario.id),
            carrera_id=_a_uuid(seminario.carrera_id),
            nombre=seminario.nombre,
            codigo=seminario.codigo,
            horas_catedra=seminario.horas_catedra,
            es_obligatorio=seminario.es_obligatorio,
            docente_email=seminario.docente_email,
            fecha_limite_actas=seminario.fecha_limite_actas,
        )
        self._session.add(modelo)
        await self._session.flush()
        return self._a_dominio(modelo)

    async def obtener_seminario(self, seminario_id: str) -> Optional[Seminario]:
        try:
            clave = _a_uuid(seminario_id)
        except ValueError:
            return None
        modelo = await self._session.get(SeminarioModel, clave)
        return self._a_dominio(modelo) if modelo else None

    async def listar(
            self, carrera_id: Optional[str] = None, solo_obligatorios: bool = False,
            docente_email: Optional[str] = None,
    ) -> list[Seminario]:
        consulta = select(SeminarioModel)
        if carrera_id is not None:
            try:
                consulta = consulta.where(SeminarioModel.carrera_id == _a_uuid(carrera_id))
            except ValueError:
                return []
        if solo_obligatorios:
            consulta = consulta.where(SeminarioModel.es_obligatorio.is_(True))
        if docente_email is not None:
            consulta = consulta.where(SeminarioModel.docente_email == docente_email)
        result = await self._session.execute(
            consulta.order_by(SeminarioModel.carrera_id, SeminarioModel.codigo)
        )
        return [self._a_dominio(m) for m in result.scalars().all()]

    async def inscribir_estudiante(self, inscripcion: InscripcionSeminario) -> InscripcionSeminario:
        modelo = InscripcionSeminarioModel(
            id=_a_uuid(inscripcion.id),
            legajo_id=_a_uuid(inscripcion.legajo_id),
            seminario_id=_a_uuid(inscripcion.seminario_id),
            nota_final=inscripcion.nota_final,
            asistencias=inscripcion.asistencias,
            total_clases=inscripcion.total_clases,
            estado=inscripcion.estado.value,
        )
        self._session.add(modelo)
        await self._session.flush()
        return self._inscripcion_a_dominio(modelo)

    async def listar_inscritos(self, seminario_id: str) -> list[EstudianteEnSeminario]:
        try:
            clave = _a_uuid(seminario_id)
        except ValueError:
            return []
        result = await self._session.execute(
            select(InscripcionSeminarioModel, LegajoModel)
            .join(LegajoModel, LegajoModel.id == InscripcionSeminarioModel.legajo_id)
            .where(InscripcionSeminarioModel.seminario_id == clave)
            .order_by(LegajoModel.apellido, LegajoModel.nombre)
        )
        return [
            EstudianteEnSeminario(
                legajo_id=str(legajo.id),
                numero_legajo=legajo.numero_legajo,
                apellido=legajo.apellido,
                nombre=legajo.nombre,
                email=legajo.email,
                nota_final=float(insc.nota_final) if insc.nota_final is not None else None,
                estado=EstadoSeminario(insc.estado),
            )
            for insc, legajo in result.all()
        ]

    async def registrar_nota_final(
            self, legajo_id: str, seminario_id: str, nota: float
    ) -> InscripcionSeminario:
        validar_nota(nota)
        result = await self._session.execute(
            select(InscripcionSeminarioModel)
            .where(InscripcionSeminarioModel.legajo_id == _a_uuid(legajo_id))
            .where(InscripcionSeminarioModel.seminario_id == _a_uuid(seminario_id))
        )
        modelo = result.scalar_one_or_none()
        if modelo is None:
            raise InscripcionSeminarioNoEncontrada(
                f"El legajo {legajo_id} no está inscripto al seminario {seminario_id}"
            )
        modelo.nota_final = nota
        modelo.estado = (EstadoSeminario.APROBADO if nota >= 4 else EstadoSeminario.DESAPROBADO).value
        await self._session.flush()
        return self._inscripcion_a_dominio(modelo)

    async def progreso_obligatorios(self, legajo_id: str) -> ProgresoSeminarios:
        clave = _a_uuid(legajo_id)
        carrera_id = await self._session.scalar(
            select(LegajoModel.carrera_id).where(LegajoModel.id == clave)
        )
        if carrera_id is None:
            return ProgresoSeminarios(obligatorios_total=0, aprobados=0)

        total = await self._session.scalar(
            select(func.count())
            .select_from(SeminarioModel)
            .where(SeminarioModel.carrera_id == carrera_id)
            .where(SeminarioModel.es_obligatorio.is_(True))
        )
        aprobados = await self._session.scalar(
            select(func.count())
            .select_from(InscripcionSeminarioModel)
            .join(SeminarioModel, SeminarioModel.id == InscripcionSeminarioModel.seminario_id)
            .where(InscripcionSeminarioModel.legajo_id == clave)
            .where(SeminarioModel.es_obligatorio.is_(True))
            .where(InscripcionSeminarioModel.estado == EstadoSeminario.APROBADO.value)
        )
        return ProgresoSeminarios(obligatorios_total=total or 0, aprobados=aprobados or 0)

    async def cursadas_de_legajo(self, legajo_id: str) -> list[CursadaDeLegajo]:
        resultado = await self._session.execute(
            select(InscripcionSeminarioModel, SeminarioModel)
            .join(SeminarioModel, SeminarioModel.id == InscripcionSeminarioModel.seminario_id)
            .where(InscripcionSeminarioModel.legajo_id == _a_uuid(legajo_id))
            .order_by(SeminarioModel.es_obligatorio.desc(), SeminarioModel.codigo)
        )
        return [
            CursadaDeLegajo(
                seminario_id=str(seminario.id),
                codigo=seminario.codigo,
                nombre=seminario.nombre,
                horas_catedra=seminario.horas_catedra,
                es_obligatorio=seminario.es_obligatorio,
                estado=EstadoSeminario(inscripcion.estado),
                nota_final=float(inscripcion.nota_final) if inscripcion.nota_final is not None else None,
            )
            for inscripcion, seminario in resultado.all()
        ]

    @staticmethod
    def _a_dominio(m: SeminarioModel) -> Seminario:
        return Seminario(
            id=str(m.id),
            carrera_id=str(m.carrera_id),
            nombre=m.nombre,
            codigo=m.codigo,
            horas_catedra=m.horas_catedra,
            es_obligatorio=m.es_obligatorio,
            docente_email=m.docente_email,
            fecha_limite_actas=m.fecha_limite_actas,
            actualizado_en=m.actualizado_en,
        )

    @staticmethod
    def _inscripcion_a_dominio(m: InscripcionSeminarioModel) -> InscripcionSeminario:
        return InscripcionSeminario(
            id=str(m.id),
            legajo_id=str(m.legajo_id),
            seminario_id=str(m.seminario_id),
            nota_final=float(m.nota_final) if m.nota_final is not None else None,
            asistencias=m.asistencias,
            total_clases=m.total_clases,
            estado=EstadoSeminario(m.estado),
        )
