from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import date

from src.shared.auth.dependencies import require_role_coordinador
from src.shared.database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from src.inscripcion.application.aprobar_legajo import aprobar_legajo
from src.inscripcion.application.observar_legajo import observar_legajo
from src.inscripcion.application.verificar_reserva_vencida import verificar_reserva_vencida
from src.inscripcion.domain.entities import EstadoLegajo, TipoCarrera
from src.shared.exceptions import LegajoNoEncontrado

router = APIRouter(tags=["Legajos - Módulo Core"])


@router.post(
    "/{legajo_id}/aprobar",
    summary="Coordinador aprueba legajo",
    description="El coordinador aprueba un legajo, genera número único y cambia estado a COMPLETADO.",
    dependencies=[Depends(require_role_coordinador())],
    tags=["Gestión Coordinador"],
)
async def api_aprobar_legajo(
        legajo_id: str,
        db: AsyncSession = Depends(get_db),
):
    """Endpoint para que el coordinador apruebe un legajo."""
    from src.inscripcion.infrastructure.orm_models import LegajoModel
    from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository

    repo = PostgresLegajoRepository(db)
    legajo_obj = await repo.obtener_por_id(legajo_id)

    legajo_actualizado, error = aprobar_legajo(legajo_obj, es_coordinador=True)

    if error:
        return JSONResponse(status_code=400, content={"error": error})

    legajo_guardado = await repo.actualizar_estado(
        legajo_id=legajo_id,
        nuevo_estado=EstadoLegajo.COMPLETADO,
        comentario="Aprobado por coordinador",
    )

    return {
        "mensaje": "Legajo aprobado exitosamente",
        "numero_legajo": legajo_guardado.numero_legajo,
        "estado": legajo_guardado.estado.value,
        "fecha_activacion": legajo_guardado.fecha_activacion,
        "mensaje_reserva": "La reserva de vacante vence a los 30 días corridos (BR-005)",
    }


@router.post(
    "/{legajo_id}/observar",
    summary="Coordinador observa legajo",
    description="El coordinador marca un legajo como observado por documentación faltante.",
    dependencies=[Depends(require_role_coordinador())],
    tags=["Gestión Coordinador"],
)
async def api_observar_legajo(
        legajo_id: str,
        comentario: str,
        db: AsyncSession = Depends(get_db),
):
    """Endpoint para que el coordinador observe un legajo."""
    from src.inscripcion.infrastructure.orm_models import LegajoModel
    from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository

    repo = PostgresLegajoRepository(db)
    legajo_obj = await repo.obtener_por_id(legajo_id)

    legajo_actualizado, error = observar_legajo(
        legajo_obj, comentario=comentario, es_coordinador=True
    )

    if error:
        return JSONResponse(status_code=400, content={"error": error})

    await repo.actualizar_estado(
        legajo_id=legajo_id,
        nuevo_estado=legajo_actualizado.estado,
        comentario=comentario,
    )

    return {
        "mensaje": "Legajo puesto en estado Observado",
        "estado_actual": legajo_actualizado.estado.value,
        "comentario": comentario,
        "proximo_paso": "Aspirante debe corregir documentación y reenviar",
    }


@router.get(
    "/{legajo_id}",
    summary="Obtener detalle de legajo",
    dependencies=[Depends(require_role_coordinador())],
    description="Obtener información de un legajo por su ID.",
    tags=["Consulta"],
)
async def api_obtener_legajo(
        legajo_id: str,
        db: AsyncSession = Depends(get_db),
):
    """Obtener detalle de un legajo."""
    from src.inscripcion.infrastructure.orm_models import LegajoModel
    from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository

    repo = PostgresLegajoRepository(db)
    legajo = await repo.obtener_por_id(legajo_id)

    return {
        "id": legajo.id,
        "numero_legajo": legajo.numero_legajo,
        "apellido_nombre": f"{legajo.apellido}, {legajo.nombre}",
        "dni": str(legajo.dni),
        "email": str(legajo.email),
        "tipo_carrera": legajo.tipo_carrera.valor,
        "estado": legajo.estado.value,
        "semaforo": legajo.semaforo,
        "fecha_inscripcion": str(legajo.fecha_inscripcion) if legajo.fecha_inscripcion else None,
    }


@router.get(
    "/",
    summary="Listar legajos con filtros",
    dependencies=[Depends(require_role_coordinador())],
    description="Listar legajos con filtros por estado, cohorte y carrera.",
    tags=["Listado"],
)
async def api_listar_legajos(
        cohorte_id: Optional[str] = None,
        estado: Optional[str] = None,
        tipo_carrera: Optional[str] = None,
        db: AsyncSession = Depends(get_db),
):
    """Listar legajos con filtros opcionales."""
    from src.inscripcion.infrastructure.orm_models import LegajoModel
    from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
    from src.inscripcion.domain.entities import EstadoLegajo as DomEstadoLegajo

    repo = PostgresLegajoRepository(db)
    legajos = await repo.listar_en_estado(DomEstadoLegajo.BORRADOR)

    if cohorte_id:
        legajos = [l for l in legajos if l.cohorte_id == cohorte_id]

    if tipo_carrera:
        legajos = [l for l in legajos if l.tipo_carrera.valor == tipo_carrera]

    return {
        "total": len(legajos),
        "legajos": [
            {
                "id": l.id,
                "numero_legajo": l.numero_legajo,
                "apellido_nombre": f"{l.apellido}, {l.nombre}",
                "dni": str(l.dni),
                "estado": l.estado.value,
                "tipo_carrera": l.tipo_carrera.valor,
            }
            for l in legajos
        ],
    }


@router.get(
    "/{legajo_id}/reserva-vencida",
    summary="Verificar si reserva de vacante venció",
    dependencies=[Depends(require_role_coordinador())],
    description="Verifica si la reserva de 30 días desde COMPLETADO ha vencido (BR-005).",
    tags=["Validación"],
)
async def api_verificar_reserva(
        legajo_id: str,
        db: AsyncSession = Depends(get_db),
):
    """Verificar estado de reserva de vacante."""
    from src.inscripcion.infrastructure.orm_models import LegajoModel
    from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository

    repo = PostgresLegajoRepository(db)
    legajo = await repo.obtener_por_id(legajo_id)

    fecha_completado = legajo.fecha_activacion or legajo.fecha_inscripcion
    if not fecha_completado:
        return {"reserva_vencida": False, "mensaje": "Legajo aún no completado"}

    hoy = date.today()
    dias_transcurridos = (hoy - fecha_completado).days
    vencido = dias_transcurridos > 30
    return {
        "reserva_vencida": vencido,
        "dias_desde_completado": dias_transcurridos,
        "mensaje": "Reserva vencida" if vencido else "Reserva vigente",
    }