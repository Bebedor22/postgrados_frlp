"""Graduación automática al aprobarse el trabajo final con todos los seminarios."""
from datetime import date
from typing import Optional

from src.carga_academica.domain.repo import SeminarioRepository
from src.inscripcion.application.gestionar_legajos import graduar_legajo
from src.inscripcion.domain.entities import EstadoLegajo
from src.inscripcion.domain.notificaciones import Notificador, SinNotificaciones
from src.inscripcion.domain.repo import LegajoRepository
from src.seguimiento_graduacion.domain.repo import TrabajoFinalRepository


def puede_graduarse(estado: EstadoLegajo, fecha_cpr: Optional[date], adeudados: int, total: int) -> bool:
    return estado == EstadoLegajo.ACTIVO and fecha_cpr is not None and total > 0 and adeudados == 0


async def graduar_si_corresponde(
        legajo_id: str,
        repo_trabajos: TrabajoFinalRepository,
        repo_seminarios: SeminarioRepository,
        repo_legajos: LegajoRepository,
        usuario_email: str,
        notificador: Notificador = SinNotificaciones(),
):
    """RF-GRAD-001: graduar si el TFI/Tesis tiene fecha CPR y no adeuda seminarios."""
    trabajo = await repo_trabajos.obtener_por_legajo(legajo_id)
    if trabajo is None or trabajo.fecha_aprobacion_cpr is None:
        return None

    legajo = await repo_legajos.obtener_por_id(legajo_id)
    progreso = await repo_seminarios.progreso_obligatorios(legajo_id)
    if not puede_graduarse(
            legajo.estado, trabajo.fecha_aprobacion_cpr, progreso.adeudados, progreso.obligatorios_total
    ):
        return None
    return await graduar_legajo(legajo_id, repo_legajos, usuario_email, notificador)
