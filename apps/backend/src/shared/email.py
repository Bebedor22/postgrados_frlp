"""Envío de emails del sistema.

EMAIL_MODO elige qué pasa con cada email:
- "smtp": se manda al servidor SMTP configurado. En desarrollo es MailHog, que
  no los entrega a nadie: se ven en http://localhost:8025.
- "simulado": no se manda nada, solo se escribe en el log del backend.

Un email que no se pudo mandar nunca rompe la operación que lo generó: se registra
el error en el log y el sistema sigue.
"""
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from src.shared.config import get_settings

logger = logging.getLogger("posgrado.email")


@dataclass
class Email:
    destinatario: str
    asunto: str
    cuerpo: str


def enviar_email(email: Email) -> bool:
    """Devuelve True si se mandó (o se simuló) sin errores."""
    settings = get_settings()
    if settings.email_modo != "smtp":
        logger.info("[EMAIL SIMULADO] Para: %s | Asunto: %s\n%s", email.destinatario, email.asunto, email.cuerpo)
        return True

    mensaje = EmailMessage()
    mensaje["From"] = settings.email_from
    mensaje["To"] = email.destinatario
    mensaje["Subject"] = email.asunto
    mensaje.set_content(email.cuerpo)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as servidor:
            servidor.send_message(mensaje)
        logger.info("Email enviado a %s: %s", email.destinatario, email.asunto)
        return True
    except (OSError, smtplib.SMTPException) as error:
        logger.error("No se pudo enviar el email a %s (%s): %s", email.destinatario, email.asunto, error)
        return False