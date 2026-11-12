"""Casos de uso del equipo de conducción sobre los legajos.

- Bandeja: listado por cohorte con filtros y búsqueda individual, y resumen por estado.
- Workflow: revisar, observar, aprobar, rechazar, matricular y dar de baja (ARQUITECTURA.md §6).
- BR-005: vencer las reservas de vacante que pasaron 30 días en COMPLETADO.

Cada cambio de estado queda en la auditoría con el email de quien lo hizo, y se
avisa al aspirante por medio del Notificador (por defecto, no se avisa nada).
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from src.gestion_documental.domain.entities import RequisitoDocumental
from src.gestion_documental.domain.repo import DocumentoRepository
from src.inscripcion.application.inscripcion_por_pasos import requisitos_de_documentos
from src.inscripcion.domain.entities import (
    DIAS_RESERVA_VACANTE,
    EstadoLegajo,
    Legajo,
    numero_de_legajo,
    prefijo_de_legajo,
)
from src.inscripcion.domain.notificaciones import Notificador, SinNotificaciones
from src.inscripcion.domain.repo import FiltrosLegajos, LegajoRepository
from src.oferta_academica.domain.repo import CohorteRepository

LARGO_MINIMO_COMENTARIO = 10
MAXIMO_EXPORTACION = 500  # PRD REQ-CORE-004: "máximo 500 registros"


class ComentarioObligatorio(ValueError):
    pass


@dataclass
class DetalleLegajo:
    legajo: Legajo
    formulario: object  # FormularioInscripcion
    historial: list
    reserva_vence_el: Optional[date]
    documentos: list[RequisitoDocumental]


# ── Bandeja ──────────────────────────────────────────────────────────────────

async def buscar_legajos(filtros: FiltrosLegajos, repo: LegajoRepository) -> tuple[list[Legajo], int]:
    return await repo.buscar(filtros)

async def legajos_para_exportar(filtros: FiltrosLegajos, repo: LegajoRepository) -> list[Legajo]:
    """Los legajos de la búsqueda actual (sin paginar), hasta 500, para bajarlos a Excel."""
    filtros.pagina, filtros.por_pagina = 1, MAXIMO_EXPORTACION
    legajos, _ = await repo.buscar(filtros)
    return legajos

async def resumen_por_estado(repo: LegajoRepository, cohorte_id: Optional[str] = None) -> dict[str, int]:
    """Cantidad de legajos por estado: alimenta el panel de "inscriptos y estado por cohorte"."""
    conteo = await repo.contar_por_estado(cohorte_id)
    return {estado.value: conteo.get(estado.value, 0) for estado in EstadoLegajo}


async def obtener_detalle(
        legajo_id: str, repo: LegajoRepository, repo_documentos: DocumentoRepository
) -> DetalleLegajo:
    legajo = await repo.obtener_por_id(legajo_id)
    formulario = await repo.obtener_formulario(legajo_id)
    reserva_vence_el = None
    if legajo.estado == EstadoLegajo.COMPLETADO:
        fecha = await repo.fecha_de_estado(legajo_id, EstadoLegajo.COMPLETADO)
        if fecha:
            reserva_vence_el = Legajo.vencimiento_de_reserva(fecha.date())
    return DetalleLegajo(
        legajo=legajo,
        formulario=formulario,
        historial=await repo.historial(legajo_id),
        reserva_vence_el=reserva_vence_el,
        documentos=await requisitos_de_documentos(legajo_id, formulario, repo_documentos),
    )


# ── Workflow ─────────────────────────────────────────────────────────────────

async def _cambiar_estado(
        legajo_id: str,
        nuevo_estado: EstadoLegajo,
        repo: LegajoRepository,
        usuario_email: Optional[str],
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


async def observar_legajo(
        legajo_id: str,
        comentario: str,
        repo: LegajoRepository,
        usuario_email: str,
        notificador: Notificador = SinNotificaciones(),
) -> Legajo:
    """PENDIENTE / EN_REVISION → OBSERVADO. El aspirante ve el comentario en su trámite y corrige."""
    comentario = _validar_comentario(comentario, "La observación")
    legajo = await _cambiar_estado(legajo_id, EstadoLegajo.OBSERVADO, repo, usuario_email, comentario)
    notificador.legajo_observado(legajo, comentario)
    return legajo


async def rechazar_legajo(
        legajo_id: str,
        motivo: str,
        repo: LegajoRepository,
        usuario_email: str,
        notificador: Notificador = SinNotificaciones(),
) -> Legajo:
    """EN_REVISION → RECHAZADO (estado terminal)."""
    motivo = _validar_comentario(motivo, "El motivo del rechazo")
    legajo = await _cambiar_estado(legajo_id, EstadoLegajo.RECHAZADO, repo, usuario_email, motivo)
    notificador.legajo_rechazado(legajo, motivo)
    return legajo


async def aprobar_legajo(
        legajo_id: str,
        repo: LegajoRepository,
        repo_cohortes: CohorteRepository,
        usuario_email: str,
        notificador: Notificador = SinNotificaciones(),
) -> Legajo:
    """EN_REVISION → COMPLETADO y asigna el número de legajo definitivo.

    Formato del SRS: AÑO-COHORTE-SECUENCIAL (ej.: 26-001-045). La cohorte es su número
    dentro del año y el secuencial es correlativo dentro de la cohorte.
    Desde este momento corre la reserva de vacante de 30 días (BR-005).
    """
    legajo = await repo.obtener_por_id(legajo_id)
    legajo.transicionar_a(EstadoLegajo.COMPLETADO)

    cohorte = await repo_cohortes.obtener_por_id(legajo.cohorte_id)
    numero_cohorte = await repo_cohortes.numero_en_el_anio(cohorte)
    secuencial = await repo.siguiente_secuencial(prefijo_de_legajo(cohorte.anio, numero_cohorte))
    numero = numero_de_legajo(cohorte.anio, numero_cohorte, secuencial)
    await repo.asignar_numero(legajo_id, numero)

    vence = Legajo.vencimiento_de_reserva(date.today())
    legajo = await repo.actualizar_estado(
        legajo_id,
        EstadoLegajo.COMPLETADO,
        f"Aprobado. Legajo N° {numero}. Reserva de vacante hasta el {vence:%d/%m/%Y}",
        usuario_email,
    )
    notificador.legajo_aprobado(legajo, vence)
    return legajo


async def matricular_legajo(
        legajo_id: str,
        repo: LegajoRepository,
        usuario_email: str,
        notificador: Notificador = SinNotificaciones(),
) -> Legajo:
    """COMPLETADO → ACTIVO: el aspirante confirmó su vacante y pasa a ser estudiante."""
    legajo = await _cambiar_estado(
        legajo_id, EstadoLegajo.ACTIVO, repo, usuario_email, "Matriculado: pasa a estudiante activo"
    )
    await repo.registrar_activacion(legajo_id, datetime.now())
    notificador.legajo_matriculado(legajo)
    return legajo


async def dar_de_baja(
        legajo_id: str,
        motivo: str,
        repo: LegajoRepository,
        usuario_email: str,
        notificador: Notificador = SinNotificaciones(),
) -> Legajo:
    """COMPLETADO / ACTIVO → BAJA (estado terminal). Pide el motivo, que queda en la auditoría."""
    motivo = _validar_comentario(motivo, "El motivo de la baja")
    legajo = await _cambiar_estado(legajo_id, EstadoLegajo.BAJA, repo, usuario_email, f"Baja: {motivo}")
    notificador.legajo_dado_de_baja(legajo, motivo)
    return legajo


async def vencer_reservas(
        repo: LegajoRepository,
        usuario_email: Optional[str],
        hoy: Optional[date] = None,
        notificador: Notificador = SinNotificaciones(),
) -> list[Legajo]:
    """BR-005: pasa a VENCIDO todo legajo que lleva más de 30 días en COMPLETADO.

    La corre todos los días la tarea programada (usuario_email = None, "automático")
    y también se puede ejecutar a mano desde la API.
    """
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
    notificador.reservas_vencidas(vencidos)
    return vencidos