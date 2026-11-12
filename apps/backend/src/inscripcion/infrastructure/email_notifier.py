"""Notificaciones del legajo por email (implementación del contrato Notificador).

Los avisos se juntan en `pendientes` y se mandan recién con `enviar_pendientes()`,
DESPUÉS de confirmar la transacción. Así nunca sale un email de algo que al final
no se guardó. En la API eso lo hace una tarea en segundo plano de FastAPI
(ver get_notificador en el router).
"""
from datetime import date

from src.inscripcion.domain.entities import Legajo
from src.inscripcion.domain.notificaciones import Notificador
from src.shared.config import get_settings
from src.shared.email import Email, enviar_email

FIRMA = "\n\nSecretaría de Posgrado\nUTN Facultad Regional La Plata"


def _saludo(legajo: Legajo) -> str:
    return f"Hola {legajo.nombre}:\n\n"


class NotificadorEmail(Notificador):
    def __init__(self):
        self.pendientes: list[Email] = []

    def _al_aspirante(self, legajo: Legajo, asunto: str, texto: str) -> None:
        self.pendientes.append(Email(str(legajo.email), asunto, _saludo(legajo) + texto + FIRMA))

    def enviar_pendientes(self) -> None:
        while self.pendientes:
            enviar_email(self.pendientes.pop(0))

    # ── Avisos ───────────────────────────────────────────────────────────────

    def inscripcion_iniciada(self, legajo: Legajo, token: str) -> None:
        link = f"{get_settings().frontend_url}/tramite/{token}"
        self._al_aspirante(
            legajo,
            "Tu inscripción al posgrado: link de seguimiento",
            "Empezaste tu inscripción. Con este link personal podés seguir completándola "
            f"cuando quieras y consultar su estado:\n\n{link}\n\n"
            "Guardalo y no lo compartas: es la única forma de entrar a tu trámite.",
        )

    def inscripcion_enviada(self, legajo: Legajo) -> None:
        self._al_aspirante(
            legajo,
            "Recibimos tu inscripción",
            "Recibimos tu inscripción. La coordinación de la carrera la va a revisar y te vamos "
            "a avisar por este medio cualquier novedad. Podés consultar el estado con tu link de seguimiento.",
        )

    def legajo_observado(self, legajo: Legajo, observacion: str) -> None:
        self._al_aspirante(
            legajo,
            "Tu inscripción tiene observaciones",
            "La coordinación revisó tu inscripción y te pide lo siguiente:\n\n"
            f"    {observacion}\n\n"
            "Entrá con tu link de seguimiento, corregí lo indicado y volvé a enviarla.",
        )

    def legajo_aprobado(self, legajo: Legajo, reserva_hasta: date) -> None:
        self._al_aspirante(
            legajo,
            "Tu inscripción fue aprobada",
            f"¡Tu inscripción fue aprobada! Tu número de legajo es {legajo.numero_legajo}.\n\n"
            f"Te reservamos la vacante hasta el {reserva_hasta:%d/%m/%Y}. Para no perderla, "
            "completá la matriculación antes de esa fecha.",
        )

    def legajo_rechazado(self, legajo: Legajo, motivo: str) -> None:
        self._al_aspirante(
            legajo,
            "Resultado de tu inscripción",
            f"Lamentamos informarte que tu inscripción no fue aceptada. Motivo:\n\n    {motivo}",
        )

    def legajo_matriculado(self, legajo: Legajo) -> None:
        self._al_aspirante(
            legajo,
            "¡Bienvenido/a al posgrado!",
            f"Ya sos estudiante activo/a. Tu número de legajo es {legajo.numero_legajo}.",
        )

    def reservas_vencidas(self, legajos: list[Legajo]) -> None:
        if not legajos:
            return
        for legajo in legajos:
            self._al_aspirante(
                legajo,
                "Venció la reserva de tu vacante",
                "Pasaron 30 días desde la aprobación de tu inscripción sin que completaras la "
                "matriculación, por lo que la reserva de tu vacante venció. Si querés retomarla, "
                "comunicate con la Secretaría de Posgrado.",
            )
        lista = "\n".join(f"- {l.numero_legajo}: {l.apellido}, {l.nombre} ({l.email})" for l in legajos)
        self.pendientes.append(Email(
            get_settings().email_coordinacion,
            f"Reservas de vacante vencidas: {len(legajos)}",
            "Los siguientes legajos pasaron a VENCIDO por no matricularse en 30 días (BR-005):\n\n"
            f"{lista}" + FIRMA,
        ))