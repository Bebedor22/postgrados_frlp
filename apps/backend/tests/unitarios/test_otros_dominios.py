"""Value objects, oferta académica, notificaciones, tareas programadas y exportación."""
import io
from datetime import datetime

import pytest
from openpyxl import load_workbook

from src.inscripcion.domain.entities import EstadoLegajo, Legajo, TipoCarrera
from src.inscripcion.domain.value_objects import DNI, Email, Pasaporte, crear_documento
from src.inscripcion.infrastructure import email_notifier
from src.inscripcion.infrastructure.email_notifier import NotificadorEmail
from src.inscripcion.infrastructure.exportador_excel import COLUMNAS, legajos_a_excel
from src.inscripcion.infrastructure.tareas_programadas import segundos_hasta_la_proxima
from src.oferta_academica.domain.entities import Carrera, Cohorte, ReglaDeNegocioViolada
from src.shared.email import Email as EmailSaliente, enviar_email


# ── Value objects ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("numero", ["1234567", "35222111"])
def test_dni_valido(numero):
    assert str(DNI(numero)) == numero


@pytest.mark.parametrize("numero", ["123456", "123456789", "35.222.111", "abc12345"])
def test_dni_invalido(numero):
    with pytest.raises(ValueError):
        DNI(numero)


def test_crear_documento():
    assert isinstance(crear_documento("DNI", "35222111"), DNI)
    assert str(crear_documento("PASAPORTE", "aab123456")) == "AAB123456"
    with pytest.raises(ValueError):
        crear_documento("LIBRETA", "123")
    with pytest.raises(ValueError):
        Pasaporte("12")


def test_email():
    assert str(Email("ana@mail.com")) == "ana@mail.com"
    with pytest.raises(ValueError):
        Email("ana-sin-arroba.com")


# ── Oferta académica ─────────────────────────────────────────────────────────

def test_carrera_valida_tipo_y_duracion():
    Carrera("1", "  Maestría  ", "Maestria", 2)
    with pytest.raises(ReglaDeNegocioViolada):
        Carrera("1", "X", "Licenciatura", 2)
    with pytest.raises(ReglaDeNegocioViolada):
        Carrera("1", "X", "Maestria", 9)
    with pytest.raises(ReglaDeNegocioViolada):
        Carrera("1", "   ", "Maestria", 2)


def test_abrir_y_cerrar_inscripcion():
    """BR-009: no se abre una inscripción abierta ni se cierra una cerrada."""
    cohorte = Cohorte("1", 2027, "Cohorte 2027")
    cohorte.abrir_inscripcion()
    assert cohorte.inscripcion_abierta
    with pytest.raises(ReglaDeNegocioViolada):
        cohorte.abrir_inscripcion()
    cohorte.cerrar_inscripcion()
    with pytest.raises(ReglaDeNegocioViolada):
        cohorte.cerrar_inscripcion()


# ── Notificaciones ───────────────────────────────────────────────────────────

def legajo(numero="27-001-001") -> Legajo:
    return Legajo("1", numero, "c", DNI("35222111"), "Rodríguez", "Ana", Email("ana@mail.com"),
                  TipoCarrera("Maestria"), False, estado=EstadoLegajo.COMPLETADO)


def test_los_emails_quedan_pendientes_hasta_enviarlos(monkeypatch):
    enviados = []
    monkeypatch.setattr(email_notifier, "enviar_email", enviados.append)
    notificador = NotificadorEmail()
    notificador.inscripcion_iniciada(legajo(), "TOKEN123")
    notificador.legajo_observado(legajo(), "Falta el título legalizado")
    assert len(notificador.pendientes) == 2 and enviados == []

    notificador.enviar_pendientes()
    assert notificador.pendientes == []
    assert "/tramite/TOKEN123" in enviados[0].cuerpo
    assert "Falta el título legalizado" in enviados[1].cuerpo
    assert enviados[1].destinatario == "ana@mail.com"


def test_reservas_vencidas_avisan_a_la_coordinacion():
    notificador = NotificadorEmail()
    notificador.reservas_vencidas([legajo("27-001-001"), legajo("27-001-002")])
    destinatarios = [e.destinatario for e in notificador.pendientes]
    assert destinatarios.count("ana@mail.com") == 2
    assert "coordinacion@posgrado.frlp.utn.edu.ar" in destinatarios
    notificador.reservas_vencidas([])
    assert len(notificador.pendientes) == 3


def test_todos_los_avisos_arman_un_email():
    notificador = NotificadorEmail()
    notificador.inscripcion_enviada(legajo())
    notificador.legajo_aprobado(legajo(), datetime(2026, 12, 10).date())
    notificador.legajo_rechazado(legajo(), "motivo")
    notificador.legajo_matriculado(legajo())
    notificador.legajo_dado_de_baja(legajo(), "motivo")
    assert len(notificador.pendientes) == 5
    assert "10/12/2026" in notificador.pendientes[1].cuerpo


def test_email_simulado_no_falla():
    assert enviar_email(EmailSaliente("a@b.com", "Asunto", "Cuerpo")) is True


# ── Tarea diaria y exportación ───────────────────────────────────────────────

def test_proxima_ejecucion_de_la_tarea_diaria():
    assert segundos_hasta_la_proxima(3, datetime(2026, 11, 10, 2, 0)) == 3600
    assert segundos_hasta_la_proxima(3, datetime(2026, 11, 10, 3, 0)) == 24 * 3600
    assert segundos_hasta_la_proxima(3, datetime(2026, 11, 10, 23, 0)) == 4 * 3600


def test_excel_con_las_columnas_del_srs():
    l = legajo()
    l.carrera_id = "car"
    l.fecha_inscripcion = datetime(2026, 11, 10, 15, 0)  # UTC
    hoja = load_workbook(io.BytesIO(legajos_a_excel([l], {"car": "Maestría"}))).active
    filas = list(hoja.iter_rows(values_only=True))
    assert list(filas[0]) == COLUMNAS
    assert filas[1][:5] == ("27-001-001", "Rodríguez, Ana", "35222111", "Aprobado", "Maestría")
    assert filas[1][5] == datetime(2026, 11, 10, 12, 0)  # Hora argentina


class SmtpFalso:
    """Reemplaza a smtplib.SMTP: guarda los mensajes en lugar de mandarlos."""
    enviados = []

    def __init__(self, host, port, timeout):
        self.destino = (host, port)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def send_message(self, mensaje):
        SmtpFalso.enviados.append(mensaje)


def test_email_por_smtp(monkeypatch):
    from src.shared import email as modulo_email
    from src.shared.config import get_settings

    monkeypatch.setattr(get_settings(), "email_modo", "smtp")
    monkeypatch.setattr(modulo_email.smtplib, "SMTP", SmtpFalso)
    assert enviar_email(EmailSaliente("ana@mail.com", "Asunto", "Cuerpo")) is True
    mensaje = SmtpFalso.enviados[-1]
    assert mensaje["To"] == "ana@mail.com" and mensaje["Subject"] == "Asunto"


def test_si_el_servidor_de_email_no_responde_no_rompe_nada(monkeypatch):
    from src.shared import email as modulo_email
    from src.shared.config import get_settings

    def servidor_caido(*args, **kwargs):
        raise ConnectionRefusedError("MailHog apagado")

    monkeypatch.setattr(get_settings(), "email_modo", "smtp")
    monkeypatch.setattr(modulo_email.smtplib, "SMTP", servidor_caido)
    assert enviar_email(EmailSaliente("ana@mail.com", "Asunto", "Cuerpo")) is False