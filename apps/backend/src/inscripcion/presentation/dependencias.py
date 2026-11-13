"""Dependencias de FastAPI compartidas por los routers de inscripción."""
from fastapi import BackgroundTasks

from src.inscripcion.infrastructure.email_notifier import NotificadorEmail


def get_notificador(tareas: BackgroundTasks) -> NotificadorEmail:
    """Notificador por email para un pedido.

    Los emails se mandan en una tarea en segundo plano, que FastAPI ejecuta después
    de enviar la respuesta. Como get_db confirma la transacción antes de responder,
    los emails salen solo si los cambios ya quedaron guardados. Si el endpoint
    termina con error, la tarea no se ejecuta y no se manda nada.
    """
    notificador = NotificadorEmail()
    tareas.add_task(notificador.enviar_pendientes)
    return notificador