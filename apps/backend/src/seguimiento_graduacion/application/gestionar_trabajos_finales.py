"""Casos de uso del trabajo final / tesis (RF-GRAD-001, BR-004)."""
from datetime import date
from typing import Optional

from src.inscripcion.domain.entities import EstadoLegajo
from src.inscripcion.domain.notificaciones import Notificador, SinNotificaciones
from src.inscripcion.domain.repo import LegajoRepository
from src.carga_academica.domain.repo import SeminarioRepository

from .gestionar_graduacion import graduar_si_corresponde
from ..domain.repo import TrabajoFinalRepository
from ..domain.trabajo_final import LegajoNoActivo, ReglaTrabajoFinalViolada, TrabajoFinal


class TrabajoFinalNoEncontrado(LookupError):
    pass


def _validar_tipo(tipo: str) -> str:
    if tipo not in ("TFI", "TESIS"):
        raise ReglaTrabajoFinalViolada("El tipo debe ser TFI o TESIS")
    return tipo


def exigir_legajo_activo(estado: EstadoLegajo) -> None:
    """Solo un legajo ACTIVO (aspirante ya aprobado y matriculado) puede tener un TFI/Tesis."""
    if estado != EstadoLegajo.ACTIVO:
        raise LegajoNoActivo(
            f"No se puede registrar el trabajo final: el legajo está {estado.value} "
            "y debe estar ACTIVO."
        )


async def registrar_trabajo_final(
        legajo_id: str,
        tipo: str,
        titulo: str,
        director_nombre: str,
        director_email: str,
        repo: TrabajoFinalRepository,
        codirector_nombre: Optional[str] = None,
        fecha_aprobacion_cpr: Optional[date] = None,
        numero_resolucion: Optional[str] = None,
) -> TrabajoFinal:
    """Crea el trabajo final del legajo, si todavía no tiene uno."""
    tipo = _validar_tipo(tipo)
    existente = await repo.obtener_por_legajo(legajo_id)
    if existente is not None:
        raise ReglaTrabajoFinalViolada(
            "El legajo ya tiene un trabajo final registrado. Usá la edición (PATCH)."
        )
    trabajo = TrabajoFinal(
        id="",
        legajo_id=legajo_id,
        tipo=tipo,  # type: ignore[arg-type]
        titulo=titulo,
        director_nombre=director_nombre,
        director_email=director_email,
        codirector_nombre=codirector_nombre,
        fecha_aprobacion_cpr=fecha_aprobacion_cpr,
        numero_resolucion=numero_resolucion,
    )
    return await repo.crear(trabajo)


async def editar_trabajo_final(
        trabajo_id: str,
        repo: TrabajoFinalRepository,
        tipo: Optional[str] = None,
        titulo: Optional[str] = None,
        director_nombre: Optional[str] = None,
        director_email: Optional[str] = None,
        codirector_nombre: Optional[str] = None,
        fecha_aprobacion_cpr: Optional[date] = None,
        numero_resolucion: Optional[str] = None,
        limpiar_fecha_cpr: bool = False,
) -> TrabajoFinal:
    trabajo = await repo.obtener_por_id(trabajo_id)
    if trabajo is None:
        raise TrabajoFinalNoEncontrado(f"No existe el trabajo final {trabajo_id}")
    if tipo is not None:
        _validar_tipo(tipo)
        trabajo.tipo = type(trabajo.tipo)(tipo)
    if titulo is not None:
        trabajo.titulo = titulo.strip()
    if director_nombre is not None:
        trabajo.director_nombre = director_nombre.strip()
    if director_email is not None:
        trabajo.director_email = director_email
    if codirector_nombre is not None:
        trabajo.codirector_nombre = codirector_nombre.strip() or None
    if limpiar_fecha_cpr:
        trabajo.fecha_aprobacion_cpr = None
    elif fecha_aprobacion_cpr is not None:
        trabajo.fecha_aprobacion_cpr = fecha_aprobacion_cpr
    if numero_resolucion is not None:
        trabajo.numero_resolucion = numero_resolucion.strip() or None

    # Revalida los campos editados con las mismas reglas del alta.
    trabajo.__post_init__()  # type: ignore[misc]
    return await repo.actualizar(trabajo)


async def graduar_con_trabajo_final(
        legajo_id: str,
        repo_seguimiento: TrabajoFinalRepository,
        repo_seminarios: SeminarioRepository,
        repo_legajos: LegajoRepository,
        usuario_email: str,
        notificador: Notificador = SinNotificaciones(),
):
    """Graduación automática: TFI/Tesis aprobado por CPR + todos los seminarios aprobados."""
    return await graduar_si_corresponde(
        legajo_id, repo_seguimiento, repo_seminarios, repo_legajos, usuario_email, notificador
    )
