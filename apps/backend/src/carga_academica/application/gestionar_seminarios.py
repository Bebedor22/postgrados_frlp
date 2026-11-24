"""Casos de uso mínimos del Módulo B que alimentan los Módulos C y D."""
import uuid
from dataclasses import dataclass
from typing import Optional

from src.carga_academica.domain.entities import (
    CursadaDeLegajo,
    EstadoSeminario,
    EstudianteEnSeminario,
    InscripcionSeminario,
    ProgresoSeminarios,
    ReglaAcademicaViolada,
    Seminario,
)
from src.carga_academica.domain.repo import SeminarioNoEncontrado, SeminarioRepository
from src.inscripcion.domain.entities import EstadoLegajo, Legajo


async def crear_seminario(
        carrera_id: str,
        nombre: str,
        codigo: str,
        horas_catedra: int,
        repo: SeminarioRepository,
        es_obligatorio: bool = True,
        docente_email: str | None = None,
        fecha_limite_actas=None,
) -> Seminario:
    seminario = Seminario(
        id=str(uuid.uuid4()),
        carrera_id=carrera_id,
        nombre=nombre,
        codigo=codigo,
        horas_catedra=horas_catedra,
        es_obligatorio=es_obligatorio,
        docente_email=docente_email,
        fecha_limite_actas=fecha_limite_actas,
    )
    return await repo.crear_seminario(seminario)


async def inscribir_estudiante(
        legajo: Legajo, seminario_id: str, repo: SeminarioRepository
) -> InscripcionSeminario:
    """Solo un estudiante ACTIVO cursa, y solo los seminarios de su propia carrera."""
    seminario = await repo.obtener_seminario(seminario_id)
    if seminario is None:
        raise SeminarioNoEncontrado(f"No existe el seminario {seminario_id}")
    if legajo.estado != EstadoLegajo.ACTIVO:
        raise ReglaAcademicaViolada(
            f"Solo un estudiante ACTIVO puede inscribirse a un seminario: el legajo está {legajo.estado.value}"
        )
    if str(legajo.carrera_id) != str(seminario.carrera_id):
        raise ReglaAcademicaViolada("El seminario es de otra carrera: el estudiante solo cursa los de la suya")
    inscripcion = InscripcionSeminario(
        id=str(uuid.uuid4()),
        legajo_id=legajo.id,
        seminario_id=seminario_id,
        estado=EstadoSeminario.CURSANDO,
    )
    return await repo.inscribir_estudiante(inscripcion)


async def listar_seminarios(
        repo: SeminarioRepository,
        carrera_id: Optional[str] = None,
        solo_obligatorios: bool = False,
        docente_email: Optional[str] = None,
) -> list[Seminario]:
    return await repo.listar(
        carrera_id=carrera_id, solo_obligatorios=solo_obligatorios, docente_email=docente_email
    )


async def listar_inscritos(
        seminario_id: str, repo: SeminarioRepository
) -> list[EstudianteEnSeminario]:
    """Los estudiantes inscriptos al seminario (para que el docente cargue actas)."""
    if await repo.obtener_seminario(seminario_id) is None:
        raise SeminarioNoEncontrado(f"No existe el seminario {seminario_id}")
    return await repo.listar_inscritos(seminario_id)


async def registrar_nota_final(
        legajo_id: str, seminario_id: str, nota: float, repo: SeminarioRepository
) -> InscripcionSeminario:
    return await repo.registrar_nota_final(legajo_id, seminario_id, nota)


async def progreso_de_seminarios(legajo_id: str, repo: SeminarioRepository) -> ProgresoSeminarios:
    return await repo.progreso_obligatorios(legajo_id)


@dataclass(frozen=True)
class AvanceAcademico:
    """Lo que ve el alumno: progreso de obligatorios y resultado de cada cursada."""

    progreso: ProgresoSeminarios
    cursadas: list[CursadaDeLegajo]


async def avance_de_legajo(legajo_id: str, repo: SeminarioRepository) -> AvanceAcademico:
    return AvanceAcademico(
        progreso=await repo.progreso_obligatorios(legajo_id),
        cursadas=await repo.cursadas_de_legajo(legajo_id),
    )
