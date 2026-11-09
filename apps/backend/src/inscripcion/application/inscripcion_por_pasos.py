"""Casos de uso de la inscripción por pasos con "cargar y guardar".

Flujo del aspirante (sin usuario ni contraseña):
1. iniciar_inscripcion  → crea el legajo en BORRADOR y devuelve un token secreto.
2. guardar_progreso     → guarda los datos de cualquier paso, todas las veces que quiera.
3. consultar_tramite    → con el token ve sus datos, el % completado y el estado.
4. confirmar_inscripcion → con el formulario completo, el legajo pasa a PENDIENTE.

El token funciona como un link personal: solo se guarda su hash (SHA-256), así que
quien lea la base de datos no puede usarlo.
"""
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from src.inscripcion.domain.entities import CambioDeEstado, EstadoLegajo, Legajo, TipoCarrera
from src.inscripcion.domain.formulario import DatosInvalidos, FormularioInscripcion
from src.inscripcion.domain.repo import LegajoRepository
from src.inscripcion.domain.value_objects import Email, crear_documento
from src.oferta_academica.application.gestionar_cohortes import verificar_cohorte_abierta
from src.oferta_academica.domain.entities import ReglaDeNegocioViolada
from src.oferta_academica.domain.repo import CarreraRepository, CohorteRepository

MAXIMO_CARRERAS_SIMULTANEAS = 2  # BR-001


class TramiteNoEncontrado(Exception):
    """Token inexistente o inválido."""


@dataclass
class Tramite:
    legajo: Legajo
    formulario: FormularioInscripcion
    historial: list[CambioDeEstado]


# ── Token de seguimiento ─────────────────────────────────────────────────────

def generar_token() -> tuple[str, str]:
    """Devuelve (token para el aspirante, hash para guardar en la base)."""
    token = secrets.token_urlsafe(32)
    return token, hashear_token(token)


def hashear_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def _legajo_por_token(token: str, repo: LegajoRepository) -> Legajo:
    legajo = await repo.obtener_por_token(hashear_token(token))
    if legajo is None:
        raise TramiteNoEncontrado()
    return legajo


# ── Casos de uso ─────────────────────────────────────────────────────────────

async def iniciar_inscripcion(
        cohorte_id: str,
        carrera_id: str,
        tipo_documento: str,
        numero_documento: str,
        nombre: str,
        apellido: str,
        email: str,
        repo: LegajoRepository,
        repo_cohortes: CohorteRepository,
        repo_carreras: CarreraRepository,
) -> tuple[Legajo, str]:
    """Paso 0: el aspirante elige carrera y cohorte y deja sus datos mínimos."""
    try:
        documento = crear_documento(tipo_documento, numero_documento.strip())
        email_vo = Email(email.strip().lower())
    except ValueError as e:
        raise DatosInvalidos(str(e))

    # BR-009: la cohorte tiene que existir y tener la inscripción abierta
    cohorte = await verificar_cohorte_abierta(cohorte_id, repo_cohortes)

    carrera = await repo_carreras.obtener_por_id(carrera_id)
    if carrera is None or not carrera.activa:
        raise ReglaDeNegocioViolada("La carrera no existe o no está activa")

    if await repo.existe_inscripcion(str(documento), cohorte.id, carrera.id):
        raise ReglaDeNegocioViolada("Ya existe una inscripción con ese documento a esta carrera en la cohorte")
    if await repo.contar_inscripciones_vigentes(str(documento), cohorte.id) >= MAXIMO_CARRERAS_SIMULTANEAS:
        raise ReglaDeNegocioViolada(
            f"Se permite inscribirse a {MAXIMO_CARRERAS_SIMULTANEAS} carreras como máximo por cohorte (BR-001)"
        )

    legajo_id = str(uuid.uuid4())
    legajo = Legajo(
        id=legajo_id,
        # Número provisorio: el definitivo se asigna cuando el coordinador aprueba
        numero_legajo=f"P-{legajo_id[:8].upper()}",
        cohorte_id=cohorte.id,
        carrera_id=carrera.id,
        tipo_documento=tipo_documento,
        dni=documento,
        apellido=apellido.strip(),
        nombre=nombre.strip(),
        email=email_vo,
        tipo_carrera=TipoCarrera(carrera.tipo),
        solicita_beca=False,
        estado=EstadoLegajo.BORRADOR,
    )
    formulario = FormularioInscripcion(
        nombre=legajo.nombre,
        apellido=legajo.apellido,
        tipo_documento=tipo_documento,
        numero_documento=str(documento),
        email=str(email_vo),
    )
    token, token_hash = generar_token()
    await repo.crear_inscripcion(legajo, formulario, token_hash)
    return legajo, token


async def guardar_progreso(
        token: str, cambios: dict, repo: LegajoRepository, hoy: Optional[date] = None
) -> Tramite:
    """Guarda los campos recibidos. Se puede llamar muchas veces ("cargar y guardar")."""
    legajo = await _legajo_por_token(token, repo)
    if not legajo.puede_editar_formulario():
        raise ReglaDeNegocioViolada(
            f"El formulario no se puede modificar con el legajo en estado {legajo.estado.value}"
        )
    # El documento identifica la inscripción: no se cambia después de iniciarla
    for campo in ("tipo_documento", "numero_documento"):
        if campo in cambios:
            raise DatosInvalidos(f"'{campo}' no se puede modificar una vez iniciada la inscripción")
    if "email" in cambios and cambios["email"]:
        try:
            cambios["email"] = str(Email(cambios["email"].strip().lower()))
        except ValueError as e:
            raise DatosInvalidos(str(e))

    formulario = await repo.obtener_formulario(legajo.id)
    formulario.actualizar(cambios, hoy)
    await repo.guardar_formulario(legajo.id, formulario)
    return await consultar_tramite(token, repo)


async def consultar_tramite(token: str, repo: LegajoRepository) -> Tramite:
    """Estado del trámite: datos cargados, % completado e historial de estados."""
    legajo = await _legajo_por_token(token, repo)
    return Tramite(
        legajo=legajo,
        formulario=await repo.obtener_formulario(legajo.id),
        historial=await repo.historial(legajo.id),
    )


async def confirmar_inscripcion(token: str, repo: LegajoRepository) -> Tramite:
    """Envía el formulario a revisión: BORRADOR (u OBSERVADO) → PENDIENTE."""
    legajo = await _legajo_por_token(token, repo)
    if not legajo.puede_editar_formulario():
        raise ReglaDeNegocioViolada(f"El legajo ya fue enviado (estado {legajo.estado.value})")

    formulario = await repo.obtener_formulario(legajo.id)
    if not formulario.esta_completo():
        faltantes = [c for campos in formulario.faltantes_por_paso().values() for c in campos]
        raise ReglaDeNegocioViolada(f"Faltan completar: {', '.join(faltantes)}")

    comentario = "Inscripción enviada por el aspirante"
    if legajo.estado == EstadoLegajo.OBSERVADO:
        comentario = "Aspirante corrigió las observaciones y reenvió"
    legajo.transicionar_a(EstadoLegajo.PENDIENTE)  # Valida el workflow del dominio
    await repo.actualizar_estado(
        legajo.id, EstadoLegajo.PENDIENTE, comentario=comentario, usuario_email=str(legajo.email)
    )
    await repo.registrar_confirmacion(legajo.id, datetime.now())
    return await consultar_tramite(token, repo)