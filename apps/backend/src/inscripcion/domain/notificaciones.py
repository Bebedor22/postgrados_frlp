"""Contrato para avisar a las personas de los cambios en un legajo (dominio puro).

Los casos de uso llaman a estos métodos sin saber CÓMO se avisa (email, log, nada).
La implementación con emails vive en infrastructure/email_notifier.py.
Esta clase base no hace nada: es la que se usa cuando no hace falta avisar
(por ejemplo, al cargar los datos de demo).
"""
from datetime import date

from .entities import Legajo


class Notificador:
    def inscripcion_iniciada(self, legajo: Legajo, token: str) -> None:
        """El aspirante empezó la inscripción: se le manda su link personal."""

    def inscripcion_enviada(self, legajo: Legajo) -> None:
        """El aspirante envió la inscripción (BORRADOR u OBSERVADO → PENDIENTE)."""

    def legajo_observado(self, legajo: Legajo, observacion: str) -> None:
        """La coordinación pidió correcciones (SRS: email con el texto de la observación)."""

    def legajo_aprobado(self, legajo: Legajo, reserva_hasta: date) -> None:
        """Aprobado: se informa el número de legajo y hasta cuándo se reserva la vacante."""

    def legajo_rechazado(self, legajo: Legajo, motivo: str) -> None:
        pass

    def legajo_matriculado(self, legajo: Legajo) -> None:
        pass

    def reservas_vencidas(self, legajos: list[Legajo]) -> None:
        """BR-005: se avisa a cada aspirante y a la coordinación (SRS: "notifica al coordinador")."""


class SinNotificaciones(Notificador):
    """No avisa nada. Es el valor por defecto de los casos de uso."""