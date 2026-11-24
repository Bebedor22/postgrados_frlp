"""API del Módulo C: trabajos finales, semáforo y legajos en riesgo.

BR-004: solo CPR crea/modifica trabajos finales.
BR-008: el coordinador puede fijar/restaurar el VERDE manualmente; el recálculo no lo pisa.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.carga_academica.infrastructure.pg_repository import PostgresSeminarioRepository
from src.inscripcion.domain.entities import EstadoLegajo
from src.inscripcion.domain.repo import FiltrosLegajos
from src.inscripcion.infrastructure.email_notifier import NotificadorEmail
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.inscripcion.presentation.dependencias import get_notificador
from src.oferta_academica.infrastructure.pg_repository import PostgresCarreraRepository
from src.shared.auth.dependencies import require_role
from src.shared.database.connection import get_db

from ..application.gestionar_trabajos_finales import (
    exigir_legajo_activo,
    graduar_con_trabajo_final,
    registrar_trabajo_final,
    editar_trabajo_final,
    TrabajoFinalNoEncontrado,
)
from ..application.recalcular_semaforos import (
    LegajoSinDatosAcademicos,
    legajos_en_riesgo,
    marcar_verde_manual,
    recalcular_legajo,
    restaurar_semaforo_automatico,
)
from ..domain.repo import FilaSeguimiento
from ..domain.trabajo_final import ReglaTrabajoFinalViolada, TrabajoFinal
from ..infrastructure.exportador_excel import exportar_en_riesgo_a_excel
from ..infrastructure.pg_repository import PostgresSeguimientoRepository, PostgresTrabajoFinalRepository
from .schemas import (
    EnRiesgoResponse, LegajoTesisItem, SemaforoManualRequest, SemaforoResponse,
    TrabajoFinalCreate, TrabajoFinalResponse, TrabajoFinalUpdate,
)

router = APIRouter()

solo_cpr = require_role("CPR")
solo_coordinador = require_role("COORDINADOR")
puede_leer = require_role("COORDINADOR", "DIRECCION", "CPR")
puede_ver_seguimiento = require_role("COORDINADOR", "DIRECCION")


def _trabajo_response(trabajo: TrabajoFinal) -> TrabajoFinalResponse:
    return TrabajoFinalResponse(
        id=trabajo.id,
        legajo_id=trabajo.legajo_id,
        tipo=trabajo.tipo.value,
        titulo=trabajo.titulo,
        director_nombre=trabajo.director_nombre,
        director_email=trabajo.director_email,
        codirector_nombre=trabajo.codirector_nombre,
        fecha_aprobacion_cpr=trabajo.fecha_aprobacion_cpr,
        numero_resolucion=trabajo.numero_resolucion,
        created_at=trabajo.created_at,
        updated_at=trabajo.updated_at,
    )


def _semaforo_response(fila: FilaSeguimiento) -> SemaforoResponse:
    return SemaforoResponse(
        legajo_id=fila.legajo_id,
        numero_legajo=fila.numero_legajo,
        apellido=fila.apellido,
        nombre=fila.nombre,
        carrera=fila.carrera_nombre,
        tipo_carrera=fila.tipo_carrera,
        fecha_inscripcion=fila.fecha_inscripcion,
        semaforo=fila.semaforo,
        semaforo_manual=fila.semaforo_manual,
        semaforo_desde=fila.semaforo_desde,
        dias_en_riesgo=fila.dias_en_riesgo(),
        seminarios_obligatorios_total=fila.seminarios_obligatorios_total,
        seminarios_aprobados=fila.seminarios_aprobados,
        seminarios_adeudados=fila.seminarios_adeudados,
        tiene_tfi_registrado=fila.tiene_tfi_registrado,
        tiene_fecha_cpr=fila.tiene_fecha_cpr,
    )


def _error_dominio(exc: Exception) -> HTTPException:
    if isinstance(exc, TrabajoFinalNoEncontrado):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    if isinstance(exc, LegajoSinDatosAcademicos):
        return HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    return HTTPException(422, str(exc))  # 422: violación de regla de dominio


@router.post(
    "/legajos/{legajo_id}/trabajo-final",
    response_model=TrabajoFinalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar TFI/Tesis (solo CPR)",
    description=(
        "BR-004: solo el rol CPR crea el trabajo final. Al aprobarlo con fecha CPR se gradúa "
        "automáticamente si no adeuda seminarios. El legajo debe existir (404 si no) y estar "
        "ACTIVO (422 si está en otro estado)."
    ),
)
async def api_registrar_trabajo_final(
        legajo_id: str,
        datos: TrabajoFinalCreate,
        db: AsyncSession = Depends(get_db, scope="function"),
        usuario: dict = Depends(solo_cpr),
        notificador: NotificadorEmail = Depends(get_notificador),
):
    # LegajoNoEncontrado lo traduce el handler global en main.py (404)
    legajo = await PostgresLegajoRepository(db).obtener_por_id(legajo_id)
    repo_trabajos = PostgresTrabajoFinalRepository(db)
    try:
        exigir_legajo_activo(legajo.estado)  # PENDIENTE, RECHAZADO, etc. → 422
        trabajo = await registrar_trabajo_final(
            legajo_id=legajo_id,
            tipo=datos.tipo,
            titulo=datos.titulo,
            director_nombre=datos.director_nombre,
            director_email=datos.director_email,
            repo=repo_trabajos,
            codirector_nombre=datos.codirector_nombre,
            fecha_aprobacion_cpr=datos.fecha_aprobacion_cpr,
            numero_resolucion=datos.numero_resolucion,
        )
        await graduar_con_trabajo_final(
            legajo_id,
            repo_trabajos,
            PostgresSeminarioRepository(db),
            PostgresLegajoRepository(db),
            usuario["email"],
            notificador,
        )
        return _trabajo_response(trabajo)
    except ReglaTrabajoFinalViolada as exc:
        raise _error_dominio(exc)


@router.patch(
    "/trabajos-finales/{trabajo_id}",
    response_model=TrabajoFinalResponse,
    summary="Modificar TFI/Tesis (solo CPR)",
    description="BR-004: solo CPR modifica título, director, fecha CPR o resolución.",
)
async def api_editar_trabajo_final(
        trabajo_id: str,
        datos: TrabajoFinalUpdate,
        db: AsyncSession = Depends(get_db, scope="function"),
        usuario: dict = Depends(solo_cpr),
        notificador: NotificadorEmail = Depends(get_notificador),
):
    repo_trabajos = PostgresTrabajoFinalRepository(db)
    try:
        trabajo = await editar_trabajo_final(
            trabajo_id,
            repo_trabajos,
            tipo=datos.tipo,
            titulo=datos.titulo,
            director_nombre=datos.director_nombre,
            director_email=datos.director_email,
            codirector_nombre=datos.codirector_nombre,
            fecha_aprobacion_cpr=datos.fecha_aprobacion_cpr,
            numero_resolucion=datos.numero_resolucion,
            limpiar_fecha_cpr=datos.limpiar_fecha_cpr,
        )
        await graduar_con_trabajo_final(
            trabajo.legajo_id,
            repo_trabajos,
            PostgresSeminarioRepository(db),
            PostgresLegajoRepository(db),
            usuario["email"],
            notificador,
        )
        return _trabajo_response(trabajo)
    except (ReglaTrabajoFinalViolada, TrabajoFinalNoEncontrado) as exc:
        raise _error_dominio(exc)


@router.get(
    "/legajos/{legajo_id}/trabajo-final",
    response_model=TrabajoFinalResponse,
    summary="Ver TFI/Tesis del legajo",
)
async def api_obtener_trabajo_final(
        legajo_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_leer),
):
    trabajo = await PostgresTrabajoFinalRepository(db).obtener_por_legajo(legajo_id)
    if trabajo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El legajo no tiene trabajo final registrado")
    return _trabajo_response(trabajo)


@router.get(
    "/legajos/{legajo_id}/semaforo",
    response_model=SemaforoResponse,
    summary="Consultar y recalcular el semáforo de un legajo",
)
async def api_semaforo(
        legajo_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(solo_coordinador),
):
    try:
        fila = await recalcular_legajo(PostgresSeguimientoRepository(db), legajo_id)
        return _semaforo_response(fila)
    except LegajoSinDatosAcademicos as exc:
        raise _error_dominio(exc)


@router.patch(
    "/legajos/{legajo_id}/semaforo/verde",
    response_model=SemaforoResponse,
    summary="Fijar o restaurar el VERDE manual (solo coordinador)",
    description=(
        "BR-008: con `manual: true` se fija VERDE y el recálculo no lo pisa. "
        "Con `manual: false` se restaura el cálculo automático."
    ),
)
async def api_verde_manual(
        legajo_id: str,
        datos: SemaforoManualRequest = SemaforoManualRequest(),
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(solo_coordinador),
):
    try:
        repo = PostgresSeguimientoRepository(db)
        fila = await (
            marcar_verde_manual(repo, legajo_id) if datos.manual
            else restaurar_semaforo_automatico(repo, legajo_id)
        )
        return _semaforo_response(fila)
    except LegajoSinDatosAcademicos as exc:
        raise _error_dominio(exc)


@router.get(
    "/graduacion/semaforo",
    response_model=EnRiesgoResponse,
    summary="Semáforo de todos los legajos activos",
    description="Alimenta el dashboard de conducción con el valor almacenado de cada legajo.",
)
async def api_semaforo_activos(
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_ver_seguimiento),
):
    filas = await PostgresSeguimientoRepository(db).listar_activos()
    return EnRiesgoResponse(total=len(filas), legajos=[_semaforo_response(fila) for fila in filas])


@router.get(
    "/graduacion/en-riesgo/exportar",
    summary="Exportar los legajos en ROJO a Excel",
    description="US-C-003: listado de estudiantes en riesgo, exportado por conducción.",
)
async def api_exportar_en_riesgo(
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_ver_seguimiento),
):
    filas = await legajos_en_riesgo(PostgresSeguimientoRepository(db))
    return Response(
        content=exportar_en_riesgo_a_excel(filas),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="estudiantes-en-riesgo.xlsx"'},
    )


@router.get(
    "/graduacion/en-riesgo",
    response_model=EnRiesgoResponse,
    summary="Legajos en ROJO ordenados por criticidad",
)
@router.get(
    "/en-riesgo",
    response_model=EnRiesgoResponse,
    summary="Alias antiguo de /graduacion/en-riesgo",
    deprecated=True,
    include_in_schema=False,
)
async def api_en_riesgo(
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_ver_seguimiento),
):
    filas = await legajos_en_riesgo(PostgresSeguimientoRepository(db))
    return EnRiesgoResponse(total=len(filas), legajos=[_semaforo_response(fila) for fila in filas])


@router.get(
    "/tesis/legajos",
    response_model=list[LegajoTesisItem],
    summary="Buscar legajos para registrar un TFI/Tesis (solo CPR)",
    description=(
        "BR-004: el CPR necesita encontrar el legajo al que le carga la tesis. "
        "Devuelve solo legajos ACTIVOS y con los datos mínimos, no la bandeja completa."
    ),
)
async def api_legajos_para_tesis(
        buscar: str = "",
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(solo_cpr),
):
    legajos, _ = await PostgresLegajoRepository(db).buscar(
        FiltrosLegajos(texto=buscar or None, estado=EstadoLegajo.ACTIVO, por_pagina=100)
    )
    carreras = {str(c.id): c.nombre for c in await PostgresCarreraRepository(db).listar()}
    repo_trabajos = PostgresTrabajoFinalRepository(db)
    return [
        LegajoTesisItem(
            legajo_id=legajo.id,
            numero_legajo=legajo.numero_legajo,
            apellido=legajo.apellido,
            nombre=legajo.nombre,
            carrera=carreras.get(legajo.carrera_id or "", ""),
            estado=legajo.estado.value,
            tiene_trabajo_final=await repo_trabajos.obtener_por_legajo(legajo.id) is not None,
        )
        for legajo in legajos
    ]
