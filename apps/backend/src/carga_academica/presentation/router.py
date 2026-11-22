"""API del Módulo B: seminarios, inscripción de estudiantes y notas finales.

Alcance mínimo aprobado: catálogo de seminarios + cursada por legajo, sin
planilla de asistencia. Estos datos son los que el Módulo C usa para el
semáforo y el Módulo D para las métricas.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.carga_academica.application.gestionar_seminarios import (
    crear_seminario,
    inscribir_estudiante,
    listar_inscritos,
    listar_seminarios,
    progreso_de_seminarios,
    registrar_nota_final,
)
from src.carga_academica.domain.entities import ReglaAcademicaViolada, Seminario
from src.carga_academica.domain.repo import (
    InscripcionSeminarioNoEncontrada,
    SeminarioNoEncontrado,
)
from src.carga_academica.infrastructure.pg_repository import PostgresSeminarioRepository
from src.carga_academica.presentation.schemas import (
    EstudianteInscripcion,
    EstudianteSeminarioResponse,
    InscripcionResponse,
    NotasFinales,
    ProgresoResponse,
    SeminarioCrear,
    SeminarioResponse,
)
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.oferta_academica.infrastructure.pg_repository import PostgresCarreraRepository
from src.shared.auth.dependencies import require_role
from src.shared.database.connection import get_db

router = APIRouter()

puede_leer = require_role("COORDINADOR", "DIRECCION", "DOCENTE")
puede_crear = require_role("COORDINADOR", "DIRECCION")


def _seminario_response(seminario: Seminario) -> SeminarioResponse:
    return SeminarioResponse(**seminario.__dict__)


def _error_dominio(exc: Exception) -> HTTPException:
    if isinstance(exc, (SeminarioNoEncontrado, InscripcionSeminarioNoEncontrada)):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    return HTTPException(422, str(exc))  # 422: violación de regla de dominio


async def _seminario_gestionable(
        seminario_id: str, usuario: dict, db: AsyncSession
) -> Seminario:
    """Carga el seminario y exige ser su docente (o conducción) para gestionarlo."""
    seminario = await PostgresSeminarioRepository(db).obtener_seminario(seminario_id)
    if seminario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe el seminario {seminario_id}")
    if usuario.get("rol") == "DOCENTE" and seminario.docente_email != usuario.get("email"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Solo el docente asignado a este seminario puede gestionarlo"
        )
    return seminario


@router.get(
    "/",
    response_model=list[SeminarioResponse],
    summary="Listar seminarios",
    description=(
        "Se puede filtrar por carrera, por docente y pedir solo los obligatorios. "
        "Un DOCENTE solo ve los suyos."
    ),
)
async def api_listar_seminarios(
        carrera_id: str | None = None,
        solo_obligatorios: bool = False,
        docente_email: str | None = None,
        db: AsyncSession = Depends(get_db, scope="function"),
        usuario: dict = Depends(puede_leer),
):
    # El docente siempre consulta los suyos: no puede ver los de otros
    if usuario.get("rol") == "DOCENTE":
        docente_email = usuario.get("email")
    seminarios = await listar_seminarios(
        PostgresSeminarioRepository(db),
        carrera_id=carrera_id, solo_obligatorios=solo_obligatorios, docente_email=docente_email,
    )
    return [_seminario_response(s) for s in seminarios]


@router.post(
    "/",
    response_model=SeminarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear seminario",
    description="Alta de seminario para una carrera (obligatorio o optativo).",
)
async def api_crear_seminario(
        datos: SeminarioCrear,
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_crear),
):
    if await PostgresCarreraRepository(db).obtener_por_id(datos.carrera_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe la carrera {datos.carrera_id}")
    try:
        seminario = await crear_seminario(
            carrera_id=datos.carrera_id,
            nombre=datos.nombre,
            codigo=datos.codigo,
            horas_catedra=datos.horas_catedra,
            repo=PostgresSeminarioRepository(db),
            es_obligatorio=datos.es_obligatorio,
            docente_email=datos.docente_email,
            fecha_limite_actas=datos.fecha_limite_actas,
        )
    except ReglaAcademicaViolada as exc:
        raise _error_dominio(exc)
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe un seminario con el código {datos.codigo}")
    return _seminario_response(seminario)


@router.get(
    "/progreso",
    response_model=ProgresoResponse,
    summary="Progreso de seminarios obligatorios de un legajo",
    description="Alimenta el semáforo del Módulo C: cuántos obligatorios adeuda el estudiante.",
)
async def api_progreso(
        legajo_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(require_role("COORDINADOR", "DIRECCION")),
):
    # LegajoNoEncontrado lo traduce el handler global en main.py (404)
    await PostgresLegajoRepository(db).obtener_por_id(legajo_id)
    progreso = await progreso_de_seminarios(legajo_id, PostgresSeminarioRepository(db))
    return ProgresoResponse(
        obligatorios_total=progreso.obligatorios_total,
        aprobados=progreso.aprobados,
        adeudados=progreso.adeudados,
    )


@router.get(
    "/{seminario_id}",
    response_model=SeminarioResponse,
    summary="Detalle de un seminario",
)
async def api_obtener_seminario(
        seminario_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        usuario: dict = Depends(puede_leer),
):
    seminario = await _seminario_gestionable(seminario_id, usuario, db)
    return _seminario_response(seminario)


@router.get(
    "/{seminario_id}/estudiantes",
    response_model=list[EstudianteSeminarioResponse],
    summary="Estudiantes inscriptos al seminario",
    description="DOCENTE del seminario, coordinación o dirección.",
)
async def api_listar_estudiantes(
        seminario_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        usuario: dict = Depends(puede_leer),
):
    try:
        await _seminario_gestionable(seminario_id, usuario, db)
        estudiantes = await listar_inscritos(seminario_id, PostgresSeminarioRepository(db))
    except SeminarioNoEncontrado as exc:
        raise _error_dominio(exc)
    return [
        EstudianteSeminarioResponse(
            legajo_id=e.legajo_id,
            numero_legajo=e.numero_legajo,
            apellido=e.apellido,
            nombre=e.nombre,
            email=e.email,
            nota_final=e.nota_final,
            estado=e.estado.value,
        )
        for e in estudiantes
    ]


@router.post(
    "/{seminario_id}/estudiantes",
    response_model=InscripcionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscribir un legajo al seminario",
)
async def api_inscribir_estudiante(
        seminario_id: str,
        datos: EstudianteInscripcion,
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_crear),
):
    # LegajoNoEncontrado lo traduce el handler global en main.py (404)
    await PostgresLegajoRepository(db).obtener_por_id(datos.legajo_id)
    try:
        inscripcion = await inscribir_estudiante(
            datos.legajo_id, seminario_id, PostgresSeminarioRepository(db)
        )
    except (SeminarioNoEncontrado, ReglaAcademicaViolada) as exc:
        raise _error_dominio(exc)
    except IntegrityError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El legajo ya está inscripto a este seminario"
        )
    return InscripcionResponse(
        id=inscripcion.id,
        legajo_id=inscripcion.legajo_id,
        seminario_id=inscripcion.seminario_id,
        nota_final=inscripcion.nota_final,
        estado=inscripcion.estado.value,
    )


@router.patch(
    "/{seminario_id}/notas",
    response_model=list[InscripcionResponse],
    summary="Cargar notas finales en lote",
    description=(
        "DOCENTE del seminario. Nota >= 4 aprueba el seminario (BR-003). "
        "Si una nota o un legajo es inválido, no se guarda ninguna."
    ),
)
async def api_registrar_notas(
        seminario_id: str,
        datos: NotasFinales,
        db: AsyncSession = Depends(get_db, scope="function"),
        usuario: dict = Depends(puede_leer),
):
    repo = PostgresSeminarioRepository(db)
    try:
        await _seminario_gestionable(seminario_id, usuario, db)
        resultados = [
            await registrar_nota_final(n.legajo_id, seminario_id, n.nota, repo)
            for n in datos.notas
        ]
    except (SeminarioNoEncontrado, InscripcionSeminarioNoEncontrada) as exc:
        raise _error_dominio(exc)
    except ReglaAcademicaViolada as exc:
        raise _error_dominio(exc)
    return [
        InscripcionResponse(
            id=i.id,
            legajo_id=i.legajo_id,
            seminario_id=i.seminario_id,
            nota_final=i.nota_final,
            estado=i.estado.value,
        )
        for i in resultados
    ]
