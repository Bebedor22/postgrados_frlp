"""Tareas que el backend corre solo (ARQUITECTURA.md §12, ADR-006).

`recalcular_semaforos` (RF-GRAD-002, BR-008, US-C-004): al arrancar y todos los días
a las 2:00 recalcula el riesgo de los legajos activos, guarda el color y avisa por
email a la coordinación cuando un legajo recién pasa a ROJO.

`vencer_reservas` (BR-005): al arrancar y todos los días a las 3:00 pasa a VENCIDO
los legajos aprobados hace más de 30 días sin matricularse y avisa a los aspirantes.

Se usa un bucle de asyncio en lugar de APScheduler (ADR-005 y ADR-006): para dos
tareas diarias alcanza y no suma dependencias.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from src.inscripcion.application.gestionar_legajos import vencer_reservas
from src.inscripcion.infrastructure.email_notifier import NotificadorEmail
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.seguimiento_graduacion.application.recalcular_semaforos import recalcular_semaforos
from src.seguimiento_graduacion.infrastructure.pg_repository import PostgresSeguimientoRepository
from src.shared.database.connection import AsyncSessionLocal

logger = logging.getLogger("posgrado.tareas")

HORA_SEMAFORO = 2  # 2:00 AM
HORA_VENCIMIENTO = 3  # 3:00 AM


async def ejecutar_vencimiento_de_reservas() -> int:
    """Corre BR-005 una vez. Devuelve cuántos legajos vencieron."""
    notificador = NotificadorEmail()
    async with AsyncSessionLocal() as session:
        # usuario_email=None: en la auditoría queda como cambio automático
        vencidos = await vencer_reservas(PostgresLegajoRepository(session), None, notificador=notificador)
        await session.commit()
    # Los emails salen recién después del commit (y sin frenar el servidor)
    await asyncio.to_thread(notificador.enviar_pendientes)
    if vencidos:
        logger.info("Reservas de vacante vencidas: %s", ", ".join(l.numero_legajo for l in vencidos))
    return len(vencidos)


async def ejecutar_recalculo_de_semaforos() -> int:
    """Corre RF-GRAD-002 una vez. Devuelve cuántos legajos cambiaron de color."""
    notificador = NotificadorEmail()
    async with AsyncSessionLocal() as session:
        resultado = await recalcular_semaforos(PostgresSeguimientoRepository(session))
        repo_legajos = PostgresLegajoRepository(session)
        for cambio in resultado.nuevos_en_riesgo:
            legajo = await repo_legajos.obtener_por_id(cambio.legajo_id)
            notificador.legajo_en_riesgo(legajo, cambio.motivo, cambio.dias_restantes)
        await session.commit()
    # El aviso sale recién después del commit, igual que el resto de los emails
    await asyncio.to_thread(notificador.enviar_pendientes)
    if resultado.actualizados:
        logger.info(
            "Semáforo recalculado: %s de %s legajos activos actualizaron su color (%s nuevos en ROJO)",
            resultado.actualizados, resultado.evaluados, len(resultado.nuevos_en_riesgo),
        )
    return resultado.actualizados


def segundos_hasta_la_proxima(hora: int, ahora: datetime) -> float:
    proxima = ahora.replace(hour=hora, minute=0, second=0, microsecond=0)
    if proxima <= ahora:
        proxima += timedelta(days=1)
    return (proxima - ahora).total_seconds()


async def _tarea_segura(tarea, mensaje: str) -> None:
    try:
        await tarea
    except Exception:  # Un error (por ejemplo, la base caída) no tiene que matar el ciclo
        logger.exception(mensaje)


async def ciclo_diario_de_tareas() -> None:
    """Al arrancar corre ambas; después, semáforo a las 2:00 y reservas a las 3:00."""
    await _tarea_segura(ejecutar_recalculo_de_semaforos(), "Falló el recálculo del semáforo")
    await _tarea_segura(ejecutar_vencimiento_de_reservas(), "Falló el vencimiento automático de reservas")

    while True:
        ahora = datetime.now()
        espera = min(
            segundos_hasta_la_proxima(HORA_SEMAFORO, ahora),
            segundos_hasta_la_proxima(HORA_VENCIMIENTO, ahora),
        )
        await asyncio.sleep(espera + 1)  # un segundo de margen para no caer justo en el límite
        hora = datetime.now().hour
        if hora == HORA_SEMAFORO:
            await _tarea_segura(ejecutar_recalculo_de_semaforos(), "Falló el recálculo del semáforo")
        elif hora == HORA_VENCIMIENTO:
            await _tarea_segura(ejecutar_vencimiento_de_reservas(), "Falló el vencimiento automático de reservas")
