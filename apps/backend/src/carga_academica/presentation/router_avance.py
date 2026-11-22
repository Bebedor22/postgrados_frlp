"""Avance académico del alumno (Módulo B), identificado por el token de su link personal.

Es un endpoint público como el resto del trámite del aspirante: el token es la credencial.
Reúne la carga académica (Módulo B), el semáforo y el trabajo final (Módulo C) en una
sola respuesta para la pantalla "Mi Avance".
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.carga_academica.application.gestionar_seminarios import avance_de_legajo
from src.carga_academica.infrastructure.pg_repository import PostgresSeminarioRepository
from src.carga_academica.presentation.schemas_avance import (
    AvanceAlumnoResponse, CursadaAlumnoResponse, ProgresoAlumnoResponse, TrabajoFinalAlumnoResponse,
)
from src.inscripcion.application.inscripcion_por_pasos import hashear_token
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.seguimiento_graduacion.infrastructure.pg_repository import (
    PostgresSeguimientoRepository, PostgresTrabajoFinalRepository,
)
from src.shared.database.connection import get_db

router = APIRouter()


@router.get(
    "/{token}/avance",
    response_model=AvanceAlumnoResponse,
    summary="Mi avance académico",
    description=(
        "Con el token del link de inscripción devuelve el progreso de seminarios "
        "obligatorios, el resultado de cada cursada, el semáforo de riesgo y el "
        "trabajo final registrado (si lo hay)."
    ),
)
async def api_avance_alumno(
        token: str,
        db: AsyncSession = Depends(get_db, scope="function"),
):
    legajo = await PostgresLegajoRepository(db).obtener_por_token(hashear_token(token))
    if legajo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trámite no encontrado: revisá el link")

    avance = await avance_de_legajo(legajo.id, PostgresSeminarioRepository(db))
    repo_seguimiento = PostgresSeguimientoRepository(db)
    fila = await repo_seguimiento.obtener_fila(legajo.id)
    trabajo = await PostgresTrabajoFinalRepository(db).obtener_por_legajo(legajo.id)

    return AvanceAlumnoResponse(
        legajo_id=legajo.id,
        numero_legajo=legajo.numero_legajo,
        estado=legajo.estado.value,
        progreso=ProgresoAlumnoResponse(
            obligatorios_total=avance.progreso.obligatorios_total,
            aprobados=avance.progreso.aprobados,
            adeudados=avance.progreso.adeudados,
        ),
        seminarios=[
            CursadaAlumnoResponse(
                seminario_id=c.seminario_id,
                codigo=c.codigo,
                nombre=c.nombre,
                horas_catedra=c.horas_catedra,
                es_obligatorio=c.es_obligatorio,
                estado=c.estado.value,
                nota_final=c.nota_final,
            )
            for c in avance.cursadas
        ],
        # ASR-003: se muestra el valor persistido (incluye el VERDE manual), nunca un cálculo local
        semaforo=fila.semaforo if fila is not None else "VERDE",
        trabajo_final=TrabajoFinalAlumnoResponse(
            tipo=trabajo.tipo.value,
            titulo=trabajo.titulo,
            director_nombre=trabajo.director_nombre,
            fecha_aprobacion_cpr=(
                trabajo.fecha_aprobacion_cpr.isoformat() if trabajo.fecha_aprobacion_cpr else None
            ),
        ) if trabajo is not None else None,
    )
