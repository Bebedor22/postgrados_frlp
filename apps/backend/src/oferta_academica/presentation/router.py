from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.oferta_academica.application.gestionar_carreras import CarreraYaExiste, crear_carrera, listar_carreras
from src.oferta_academica.application.gestionar_cohortes import (
    CohorteNoEncontrada,
    CohorteYaExiste,
    cambiar_estado_inscripcion,
    crear_cohorte,
    listar_cohortes,
)
from src.oferta_academica.domain.entities import ReglaDeNegocioViolada
from src.oferta_academica.infrastructure.pg_repository import PostgresCarreraRepository, PostgresCohorteRepository
from src.oferta_academica.presentation.schemas import (
    CambioInscripcion,
    CarreraCrear,
    CarreraResponse,
    CohorteCrear,
    CohorteResponse,
)
from src.shared.auth.dependencies import require_role
from src.shared.database.connection import get_db

router_carreras = APIRouter()
router_cohortes = APIRouter()


# ── Carreras ─────────────────────────────────────────────────────────────────

@router_carreras.get(
    "/",
    response_model=list[CarreraResponse],
    summary="Listar carreras activas",
    description="Público: lo usa el formulario de inscripción para que el aspirante elija la carrera.",
)
async def api_listar_carreras(db: AsyncSession = Depends(get_db, scope="function")):
    carreras = await listar_carreras(PostgresCarreraRepository(db))
    return [CarreraResponse(**asdict(c)) for c in carreras]


@router_carreras.post(
    "/",
    response_model=CarreraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear carrera",
    description="Solo la Dirección de Posgrado o el equipo de conducción.",
    dependencies=[Depends(require_role("DIRECCION", "COORDINADOR"))],
)
async def api_crear_carrera(datos: CarreraCrear, db: AsyncSession = Depends(get_db, scope="function")):
    try:
        carrera = await crear_carrera(datos.nombre, datos.tipo, datos.duracion_anios, PostgresCarreraRepository(db))
    except CarreraYaExiste as e:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe la carrera '{e}'")
    except ReglaDeNegocioViolada as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return CarreraResponse(**asdict(carrera))


# ── Cohortes ─────────────────────────────────────────────────────────────────

@router_cohortes.get(
    "/",
    response_model=list[CohorteResponse],
    summary="Listar cohortes",
    description="Público. Con `solo_abiertas=true` devuelve solo las que aceptan inscripciones.",
)
async def api_listar_cohortes(solo_abiertas: bool = False, db: AsyncSession = Depends(get_db, scope="function")):
    cohortes = await listar_cohortes(PostgresCohorteRepository(db), solo_abiertas=solo_abiertas)
    return [CohorteResponse(**asdict(c)) for c in cohortes]


@router_cohortes.post(
    "/",
    response_model=CohorteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cohorte",
    description="La cohorte se crea con la inscripción cerrada.",
    dependencies=[Depends(require_role("COORDINADOR"))],
)
async def api_crear_cohorte(datos: CohorteCrear, db: AsyncSession = Depends(get_db, scope="function")):
    try:
        cohorte = await crear_cohorte(datos.anio, datos.nombre, PostgresCohorteRepository(db), datos.fecha_inicio)
    except CohorteYaExiste as e:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe la cohorte '{e}'")
    return CohorteResponse(**asdict(cohorte))


@router_cohortes.patch(
    "/{cohorte_id}/inscripcion",
    response_model=CohorteResponse,
    summary="Abrir o cerrar la inscripción de una cohorte (BR-009)",
    dependencies=[Depends(require_role("COORDINADOR"))],
)
async def api_cambiar_inscripcion(cohorte_id: str, datos: CambioInscripcion, db: AsyncSession = Depends(get_db, scope="function")):
    try:
        cohorte = await cambiar_estado_inscripcion(cohorte_id, datos.abierta, PostgresCohorteRepository(db))
    except CohorteNoEncontrada:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cohorte no encontrada")
    except ReglaDeNegocioViolada as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return CohorteResponse(**asdict(cohorte))