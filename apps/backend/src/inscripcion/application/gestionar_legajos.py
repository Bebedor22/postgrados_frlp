"""Casos de uso del equipo de conducción sobre los legajos.

- Bandeja: listado por cohorte con filtros y búsqueda individual, y resumen por estado.
- Workflow: revisar, observar, aprobar, rechazar y matricular (ARQUITECTURA.md §6).
- BR-005: vencer las reservas de vacante que pasaron 30 días en COMPLETADO.

Cada cambio de estado queda en la auditoría con el email de quien lo hizo.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from src.inscripcion.domain.entities import DIAS_RESERVA_VACANTE, EstadoLegajo, Legajo
from src.inscripcion.domain.repo import FiltrosLegajos, LegajoRepository
from src.oferta_academica.domain.repo import CohorteRepository

LARGO_MINIMO_COMENTARIO = 10


class ComentarioObligatorio(ValueError):
    pass


@dataclass
class DetalleLegajo:
    legajo: Legajo
    formulario: object  # FormularioInscripcion
    historial: list
    reserva_vence_el: Optional[date]


# ── Bandeja ──────────────────────────────────────────────────────────────────

async def buscar_legajos(filtros: FiltrosLegajos, repo: LegajoRepository) -> tuple[list[Legajo], int]:
    return await repo.buscar(filtros)


async def resumen_por_estado(repo: LegajoRepository, cohorte_id: Optional[str] = None) -> dict[str, int]:
    """Cantidad de legajos por estado: alimenta el panel de "inscriptos y estado por cohorte"."""
    conteo = await repo.contar_por_estado(cohorte_id)
    return {estado.value: conteo.get(estado.value, 0) for estado in EstadoLegajo}


async def obtener_detalle(legajo_id: str, repo: LegajoRepository) -> DetalleLegajo:
    legajo = await repo.obtener_por_id(legajo_id)
    reserva_vence_el = None
    if legajo.estado == EstadoLegajo.COMPLETADO:
        fecha = await repo.fecha_de_estado(legajo_id, EstadoLegajo.COMPLETADO)
        if fecha:
            reserva_vence_el = Legajo.vencimiento_de_reserva(fecha.date())
    return DetalleLegajo(
        legajo=legajo,
        formulario=await repo.obtener_formulario(legajo_id),
        historial=await repo.historial(legajo_id),
        reserva_vence_el=reserva_vence_el,
    )


# ── Workflow ─────────────────────────────────────────────────────────────────

async def _cambiar_estado(
        legajo_id: str,
        nuevo_estado: EstadoLegajo,
        repo: LegajoRepository,
        usuario_email: str,
        comentario: Optional[str],
) -> Legajo:
    legajo = await repo.obtener_por_id(legajo_id)
    legajo.transicionar_a(nuevo_estado)  # Lanza TransicionInvalida si el workflow no lo permite
    return await repo.actualizar_estado(legajo_id, nuevo_estado, comentario, usuario_email)


def _validar_comentario(texto: Optional[str], que: str) -> str:
    texto = (texto or "").strip()
    if len(texto) < LARGO_MINIMO_COMENTARIO:
        raise ComentarioObligatorio(f"{que} debe tener al menos {LARGO_MINIMO_COMENTARIO} caracteres")
    return texto


async def revisar_legajo(legajo_id: str, repo: LegajoRepository, usuario_email: str) -> Legajo:
    """PENDIENTE → EN_REVISION: el coordinador toma el legajo para revisarlo."""
    return await _cambiar_estado(
        legajo_id, EstadoLegajo.EN_REVISION, repo, usuario_email, "Legajo tomado para revisión"
    )


async def observar_legajo(legajo_id: str, comentario: str, repo: LegajoRepository, usuario_email: str) -> Legajo:
    """PENDIENTE / EN_REVISION → OBSERVADO. El aspirante ve el comentario en su trámite y corrige."""
    comentario = _validar_comentario(comentario, "La observación")
    return await _cambiar_estado(legajo_id, EstadoLegajo.OBSERVADO, repo, usuario_email, comentario)


async def rechazar_legajo(legajo_id: str, motivo: str, repo: LegajoRepository, usuario_email: str) -> Legajo:
    """EN_REVISION → RECHAZADO (estado terminal)."""
    motivo = _validar_comentario(motivo, "El motivo del rechazo")
    return await _cambiar_estado(legajo_id, EstadoLegajo.RECHAZADO, repo, usuario_email, motivo)


async def aprobar_legajo(
        legajo_id: str,
        repo: LegajoRepository,
        repo_cohortes: CohorteRepository,
        usuario_email: str,
) -> Legajo:
    """EN_REVISION → COMPLETADO y asigna el número de legajo definitivo (AA-NNNN).

    AA son los dos últimos dígitos del año de la cohorte y NNNN es correlativo dentro
    de ese año. Desde este momento corre la reserva de vacante de 30 días (BR-005).
    """
    legajo = await repo.obtener_por_id(legajo_id)
    legajo.transicionar_a(EstadoLegajo.COMPLETADO)

    cohorte = await repo_cohortes.obtener_por_id(legajo.cohorte_id)
    prefijo = f"{cohorte.anio % 100:02d}-"
    numero = f"{prefijo}{await repo.siguiente_secuencial(prefijo):04d}"
    await repo.asignar_numero(legajo_id, numero)

    vence = Legajo.vencimiento_de_reserva(date.today())
    return await repo.actualizar_estado(
        legajo_id,
        EstadoLegajo.COMPLETADO,
        f"Aprobado. Legajo N° {numero}. Reserva de vacante hasta el {vence:%d/%m/%Y}",
        usuario_email,
    )


async def matricular_legajo(legajo_id: str, repo: LegajoRepository, usuario_email: str) -> Legajo:
    """COMPLETADO → ACTIVO: el aspirante confirmó su vacante y pasa a ser estudiante."""
    legajo = await _cambiar_estado(
        legajo_id, EstadoLegajo.ACTIVO, repo, usuario_email, "Matriculado: pasa a estudiante activo"
    )
    await repo.registrar_activacion(legajo_id, datetime.now())
    return legajo


async def vencer_reservas(repo: LegajoRepository, usuario_email: str, hoy: Optional[date] = None) -> list[Legajo]:
    """BR-005: pasa a VENCIDO todo legajo que lleva más de 30 días en COMPLETADO."""
    hoy = hoy or date.today()
    limite = datetime.combine(hoy - timedelta(days=DIAS_RESERVA_VACANTE), datetime.min.time())
    vencidos = []
    for legajo in await repo.listar_en_estado_desde_antes_de(EstadoLegajo.COMPLETADO, limite):
        vencidos.append(
            await _cambiar_estado(
                legajo.id,
                EstadoLegajo.VENCIDO,
                repo,
                usuario_email,
                f"Reserva de vacante vencida ({DIAS_RESERVA_VACANTE} días sin matricularse)",
            )
        )
    return vencidos