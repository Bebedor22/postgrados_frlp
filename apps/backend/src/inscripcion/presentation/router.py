"""Bandeja del equipo de conducción: listado, búsqueda, detalle y workflow de legajos.

Lectura: COORDINADOR y DIRECCION (el enunciado da acceso a la conducción y a las
autoridades). Cambios de estado: solo COORDINADOR.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.inscripcion.application.gestionar_legajos import (
    ComentarioObligatorio,
    aprobar_legajo,
    buscar_legajos,
    matricular_legajo,
    obtener_detalle,
    observar_legajo,
    rechazar_legajo,
    resumen_por_estado,
    revisar_legajo,
    vencer_reservas,
)
from src.inscripcion.domain.entities import EstadoLegajo, Legajo, TransicionInvalida
from src.inscripcion.domain.repo import FiltrosLegajos
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.inscripcion.presentation.presentadores import tramite_a_respuesta
from src.inscripcion.presentation.schemas_legajos import (
    CambioEstadoResponse,
    ComentarioRequest,
    LegajoDetalleResponse,
    LegajoFila,
    ListadoLegajosResponse,
    MotivoRequest,
    ReservasVencidasResponse,
)
from src.oferta_academica.infrastructure.pg_repository import PostgresCarreraRepository, PostgresCohorteRepository
from src.shared.auth.dependencies import require_role
from src.shared.database.connection import get_db

router = APIRouter()

puede_leer = require_role("COORDINADOR", "DIRECCION")
puede_gestionar = require_role("COORDINADOR")


def _respuesta_cambio(legajo: Legajo) -> CambioEstadoResponse:
    return CambioEstadoResponse(legajo_id=legajo.id, numero_legajo=legajo.numero_legajo, estado=legajo.estado.value)


async def _ejecutar(caso_de_uso):
    """Traduce los errores del dominio a códigos HTTP."""
    try:
        return await caso_de_uso
    except TransicionInvalida as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    except ComentarioObligatorio as e:
        raise HTTPException(422, str(e))


# ── Bandeja ──────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=ListadoLegajosResponse,
    summary="Listar inscriptos con filtros y búsqueda",
    description="Filtra por cohorte, carrera y estado. `buscar` busca en apellido, nombre, documento, email y N° de legajo.",
)
async def api_listar_legajos(
        cohorte_id: Optional[str] = None,
        carrera_id: Optional[str] = None,
        estado: Optional[EstadoLegajo] = None,
        buscar: Optional[str] = Query(None, min_length=2),
        pagina: int = Query(1, ge=1),
        por_pagina: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_leer),
):
    filtros = FiltrosLegajos(cohorte_id, carrera_id, estado, buscar, pagina, por_pagina)
    legajos, total = await buscar_legajos(filtros, PostgresLegajoRepository(db))
    carreras = {c.id: c.nombre for c in await PostgresCarreraRepository(db).listar(solo_activas=False)}
    return ListadoLegajosResponse(
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        legajos=[
            LegajoFila(
                id=l.id,
                numero_legajo=l.numero_legajo,
                apellido=l.apellido,
                nombre=l.nombre,
                tipo_documento=l.tipo_documento,
                documento=str(l.dni),
                email=str(l.email),
                carrera_id=l.carrera_id,
                carrera=carreras.get(l.carrera_id),
                estado=l.estado.value,
                solicita_beca=l.solicita_beca,
                tipo_beca=l.tipo_beca,
                fecha_inscripcion=l.fecha_inscripcion,
            )
            for l in legajos
        ],
    )


@router.get(
    "/resumen",
    response_model=dict[str, int],
    summary="Cantidad de legajos por estado",
    description="Para el panel de conducción: inscriptos y estado por cohorte.",
)
async def api_resumen(
        cohorte_id: Optional[str] = None,
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_leer),
):
    return await resumen_por_estado(PostgresLegajoRepository(db), cohorte_id)


@router.post(
    "/vencer-reservas",
    response_model=ReservasVencidasResponse,
    summary="Vencer reservas de vacante (BR-005)",
    description="Pasa a VENCIDO los legajos que llevan más de 30 días en COMPLETADO sin matricularse.",
)
async def api_vencer_reservas(db: AsyncSession = Depends(get_db, scope="function"), usuario: dict = Depends(puede_gestionar)):
    vencidos = await vencer_reservas(PostgresLegajoRepository(db), usuario["email"])
    return ReservasVencidasResponse(cantidad=len(vencidos), legajos=[_respuesta_cambio(l) for l in vencidos])


@router.get(
    "/{legajo_id}",
    response_model=LegajoDetalleResponse,
    summary="Detalle completo de un legajo",
    description="Todos los datos del formulario, el % completado, el historial de estados y la reserva de vacante.",
)
async def api_detalle_legajo(legajo_id: str, db: AsyncSession = Depends(get_db, scope="function"), _usuario: dict = Depends(puede_leer)):
    detalle = await obtener_detalle(legajo_id, PostgresLegajoRepository(db))
    base = tramite_a_respuesta(detalle.legajo, detalle.formulario, detalle.historial)
    return LegajoDetalleResponse(**base.model_dump(), reserva_vence_el=detalle.reserva_vence_el)


# ── Workflow (solo COORDINADOR) ──────────────────────────────────────────────

@router.post("/{legajo_id}/revisar", response_model=CambioEstadoResponse, summary="Tomar para revisión (PENDIENTE → EN_REVISION)")
async def api_revisar(legajo_id: str, db: AsyncSession = Depends(get_db, scope="function"), usuario: dict = Depends(puede_gestionar)):
    return _respuesta_cambio(await _ejecutar(revisar_legajo(legajo_id, PostgresLegajoRepository(db), usuario["email"])))


@router.post(
    "/{legajo_id}/observar",
    response_model=CambioEstadoResponse,
    summary="Observar (→ OBSERVADO)",
    description="El aspirante ve el comentario en su trámite, corrige y vuelve a enviar.",
)
async def api_observar(
        legajo_id: str, datos: ComentarioRequest, db: AsyncSession = Depends(get_db, scope="function"), usuario: dict = Depends(puede_gestionar)
):
    caso = observar_legajo(legajo_id, datos.comentario, PostgresLegajoRepository(db), usuario["email"])
    return _respuesta_cambio(await _ejecutar(caso))


@router.post(
    "/{legajo_id}/aprobar",
    response_model=CambioEstadoResponse,
    summary="Aprobar (EN_REVISION → COMPLETADO)",
    description="Asigna el número de legajo definitivo (AA-NNNN) y empieza a correr la reserva de vacante de 30 días.",
)
async def api_aprobar(legajo_id: str, db: AsyncSession = Depends(get_db, scope="function"), usuario: dict = Depends(puede_gestionar)):
    caso = aprobar_legajo(legajo_id, PostgresLegajoRepository(db), PostgresCohorteRepository(db), usuario["email"])
    return _respuesta_cambio(await _ejecutar(caso))


@router.post("/{legajo_id}/rechazar", response_model=CambioEstadoResponse, summary="Rechazar (EN_REVISION → RECHAZADO)")
async def api_rechazar(
        legajo_id: str, datos: MotivoRequest, db: AsyncSession = Depends(get_db, scope="function"), usuario: dict = Depends(puede_gestionar)
):
    caso = rechazar_legajo(legajo_id, datos.motivo, PostgresLegajoRepository(db), usuario["email"])
    return _respuesta_cambio(await _ejecutar(caso))


@router.post("/{legajo_id}/matricular", response_model=CambioEstadoResponse, summary="Matricular (COMPLETADO → ACTIVO)")
async def api_matricular(legajo_id: str, db: AsyncSession = Depends(get_db, scope="function"), usuario: dict = Depends(puede_gestionar)):
    return _respuesta_cambio(await _ejecutar(matricular_legajo(legajo_id, PostgresLegajoRepository(db), usuario["email"])))