"""API del Módulo D: dashboard de estadísticas y exportación a Excel."""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.dependencies import require_role
from src.shared.database.connection import get_db

from ..application.consultar_metricas import (
    CohorteNoEncontrada,
    dashboard,
    dashboard_para_exportar,
    metricas_por_cohorte,
)
from ..domain.metricas import MetricasCohorte
from ..infrastructure.exportador_excel import exportar_dashboard_a_excel
from ..infrastructure.pg_repository import PostgresMetricasRepository
from .schemas import DashboardResponse, MetricasCohorteResponse

router = APIRouter()

puede_leer = require_role("COORDINADOR", "DIRECCION")


def _cohorte_response(metricas: MetricasCohorte) -> MetricasCohorteResponse:
    return MetricasCohorteResponse(
        cohorte_id=metricas.cohorte_id,
        cohorte_nombre=metricas.cohorte_nombre,
        cohorte_anio=metricas.cohorte_anio,
        inscriptos=metricas.inscriptos,
        activos=metricas.activos,
        graduados=metricas.graduados,
        bajas=metricas.bajas,
        en_riesgo=metricas.en_riesgo,
        retencion_pct=metricas.retencion_pct,
        desgranamiento_pct=metricas.desgranamiento_pct,
        tiempo_promedio_graduacion_dias=metricas.tiempo_promedio_graduacion_dias,
    )


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Métricas globales y por cohorte",
    description=(
        "Inscriptos, retención, desgranamiento, graduados, tiempo promedio de graduación y "
        "estudiantes en riesgo (RF-REP-001)."
    ),
)
async def api_dashboard(
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_leer),
):
    metricas = await dashboard(PostgresMetricasRepository(db))
    return DashboardResponse(
        total_inscriptos=metricas.total_inscriptos,
        activos=metricas.activos,
        graduados=metricas.graduados,
        bajas=metricas.bajas,
        en_riesgo=metricas.en_riesgo,
        retencion_pct=metricas.retencion_pct,
        desgranamiento_pct=metricas.desgranamiento_pct,
        tiempo_promedio_graduacion_dias=metricas.tiempo_promedio_graduacion_dias,
        por_estado=metricas.por_estado,
        por_tipo_carrera=metricas.por_tipo_carrera,
        cohortes=[_cohorte_response(c) for c in metricas.cohortes],
    )


@router.get(
    "/cohortes/{cohorte_id}",
    response_model=MetricasCohorteResponse,
    summary="Métricas de una cohorte",
)
async def api_metricas_cohorte(
        cohorte_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_leer),
):
    try:
        return _cohorte_response(
            await metricas_por_cohorte(PostgresMetricasRepository(db), cohorte_id)
        )
    except CohorteNoEncontrada as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.get(
    "/exportar",
    summary="Exportar dashboard a Excel",
    description="RF-REP-002: headers en negrita, anchos ajustados, filtros y hoja de metadatos.",
    responses={200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}}},
)
async def api_exportar(
        db: AsyncSession = Depends(get_db, scope="function"),
        _usuario: dict = Depends(puede_leer),
):
    metricas = await dashboard_para_exportar(PostgresMetricasRepository(db))
    contenido = exportar_dashboard_a_excel(metricas)
    return Response(
        content=contenido,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="metricas_posgrado.xlsx"'},
    )
