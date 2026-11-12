"""Tareas que el backend corre solo (ARQUITECTURA.md §12).

`vencer_reservas` (BR-005): todos los días a las 3:00 pasa a VENCIDO los legajos
que llevan más de 30 días aprobados sin matricularse, y avisa por email al aspirante
y a la coordinación. También corre una vez al arrancar el backend, así no se pierde
un día si el servidor estuvo apagado a esa hora.

Se usa un bucle de asyncio en lugar de una librería (APScheduler, cron): para una
sola tarea diaria alcanza y no suma dependencias.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from src.inscripcion.application.gestionar_legajos import vencer_reservas
from src.inscripcion.infrastructure.email_notifier import NotificadorEmail
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.shared.database.connection import AsyncSessionLocal

logger = logging.getLogger("posgrado.tareas")

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


def segundos_hasta_la_proxima(hora: int, ahora: datetime) -> float:
    proxima = ahora.replace(hour=hora, minute=0, second=0, microsecond=0)
    if proxima <= ahora:
        proxima += timedelta(days=1)
    return (proxima - ahora).total_seconds()


async def ciclo_diario_de_vencimientos() -> None:
    """Corre al arrancar y después todos los días a las HORA_VENCIMIENTO. Nunca termina."""
    while True:
        try:
            await ejecutar_vencimiento_de_reservas()
        except Exception:  # Un error (por ejemplo, la base caída) no tiene que matar el ciclo
            logger.exception("Falló el vencimiento automático de reservas")
        await asyncio.sleep(segundos_hasta_la_proxima(HORA_VENCIMIENTO, datetime.now()))