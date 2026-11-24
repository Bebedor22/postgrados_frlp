"""Casos de uso del dashboard de estadísticas (RF-REP-001)."""
from typing import Optional

from ..domain.metricas import MetricasCohorte, MetricasDashboard, calcular_dashboard
from ..domain.repo import MetricasRepository


class CohorteNoEncontrada(LookupError):
    pass


async def dashboard(repo: MetricasRepository, tipo_carrera: Optional[str] = None) -> MetricasDashboard:
    """Métricas globales y por cohorte; `tipo_carrera` filtra (Especializacion/Maestria/Doctorado)."""
    legajos = await repo.cargar_legajos(tipo_carrera=tipo_carrera)
    return calcular_dashboard(legajos, await repo.listar_cohortes())


async def metricas_por_cohorte(repo: MetricasRepository, cohorte_id: str) -> MetricasCohorte:
    cohortes = await repo.listar_cohortes()
    cohorte = next((c for c in cohortes if c.id == cohorte_id), None)
    if cohorte is None:
        raise CohorteNoEncontrada(f"No existe la cohorte {cohorte_id}")
    dashboard_completo = calcular_dashboard(await repo.cargar_legajos(cohorte_id), [cohorte])
    return dashboard_completo.cohortes[0]


async def dashboard_para_exportar(
        repo: MetricasRepository, tipo_carrera: Optional[str] = None
) -> MetricasDashboard:
    return await dashboard(repo, tipo_carrera)
