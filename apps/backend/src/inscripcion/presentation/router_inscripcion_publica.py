"""Endpoints públicos del aspirante: inscripción por pasos y estado del trámite.

No requieren usuario: el aspirante se identifica con el token de su link personal.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.inscripcion.application.inscripcion_por_pasos import (
    Tramite,
    TramiteNoEncontrado,
    confirmar_inscripcion,
    consultar_tramite,
    guardar_progreso,
    iniciar_inscripcion,
)
from src.inscripcion.domain.formulario import DatosInvalidos
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.inscripcion.presentation.presentadores import tramite_a_respuesta
from src.inscripcion.presentation.schemas_inscripcion import (
    DatosFormulario,
    InicioInscripcion,
    InscripcionIniciadaResponse,
    TramiteResponse,
)
from src.oferta_academica.application.gestionar_cohortes import CohorteNoEncontrada
from src.oferta_academica.domain.entities import ReglaDeNegocioViolada
from src.oferta_academica.infrastructure.pg_repository import PostgresCarreraRepository, PostgresCohorteRepository
from src.shared.config import get_settings
from src.shared.database.connection import get_db

router = APIRouter()


def _a_respuesta(tramite: Tramite) -> TramiteResponse:
    return tramite_a_respuesta(tramite.legajo, tramite.formulario, tramite.historial)


def _error_http(error: Exception) -> HTTPException:
    if isinstance(error, TramiteNoEncontrado):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Trámite no encontrado: revisá el link")
    if isinstance(error, CohorteNoEncontrada):
        return HTTPException(status.HTTP_404_NOT_FOUND, "La cohorte no existe")
    if isinstance(error, DatosInvalidos):
        return HTTPException(422, str(error))  # Datos con formato inválido
    return HTTPException(status.HTTP_409_CONFLICT, str(error))


@router.post(
    "/",
    response_model=InscripcionIniciadaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar inscripción",
    description=(
        "Crea el legajo en BORRADOR y devuelve un **token** y un link personal para retomar la "
        "inscripción y consultar su estado. Valida cohorte abierta (BR-009) y máximo 2 carreras (BR-001)."
    ),
)
async def api_iniciar_inscripcion(datos: InicioInscripcion, db: AsyncSession = Depends(get_db)):
    try:
        legajo, token = await iniciar_inscripcion(
            **datos.model_dump(),
            repo=PostgresLegajoRepository(db),
            repo_cohortes=PostgresCohorteRepository(db),
            repo_carreras=PostgresCarreraRepository(db),
        )
    except (DatosInvalidos, ReglaDeNegocioViolada, CohorteNoEncontrada) as e:
        raise _error_http(e)
    return InscripcionIniciadaResponse(
        legajo_id=legajo.id,
        estado=legajo.estado.value,
        token=token,
        link_seguimiento=f"{get_settings().frontend_url}/tramite/{token}",
    )


@router.get(
    "/{token}",
    response_model=TramiteResponse,
    summary="Estado del trámite",
    description="Datos cargados, porcentaje completado, campos faltantes por paso e historial de estados.",
)
async def api_consultar_tramite(token: str, db: AsyncSession = Depends(get_db)):
    try:
        return _a_respuesta(await consultar_tramite(token, PostgresLegajoRepository(db)))
    except TramiteNoEncontrado as e:
        raise _error_http(e)


@router.patch(
    "/{token}",
    response_model=TramiteResponse,
    summary="Guardar progreso (cargar y guardar)",
    description="Guarda solo los campos enviados. Se puede llamar en cada paso del wizard, todas las veces que haga falta.",
)
async def api_guardar_progreso(token: str, datos: DatosFormulario, db: AsyncSession = Depends(get_db)):
    try:
        cambios = datos.model_dump(exclude_unset=True)
        return _a_respuesta(await guardar_progreso(token, cambios, PostgresLegajoRepository(db)))
    except (TramiteNoEncontrado, DatosInvalidos, ReglaDeNegocioViolada) as e:
        raise _error_http(e)


@router.post(
    "/{token}/confirmar",
    response_model=TramiteResponse,
    summary="Enviar la inscripción a revisión",
    description="Con el formulario completo, el legajo pasa de BORRADOR (u OBSERVADO) a PENDIENTE.",
)
async def api_confirmar_inscripcion(token: str, db: AsyncSession = Depends(get_db)):
    try:
        return _a_respuesta(await confirmar_inscripcion(token, PostgresLegajoRepository(db)))
    except (TramiteNoEncontrado, ReglaDeNegocioViolada) as e:
        raise _error_http(e)