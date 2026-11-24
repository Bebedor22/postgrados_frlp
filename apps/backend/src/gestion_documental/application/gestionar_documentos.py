"""Casos de uso de los documentos del legajo.

- El aspirante sube, reemplaza y borra sus PDFs con el token de su link personal,
  solo mientras puede editar el legajo (BORRADOR u OBSERVADO).
- La conducción (coordinación y Dirección) descarga cualquier documento.
- Antes de entregar un archivo se verifica que su checksum coincida con el
  registrado al subirlo (integridad).
"""
import os
import uuid
from datetime import datetime

from src.gestion_documental.domain.entities import (
    ArchivoInvalido,
    Documento,
    DocumentoNoEncontrado,
    TipoDocumento,
    calcular_checksum,
    validar_pdf,
)
from src.gestion_documental.domain.repo import AlmacenamientoArchivos, DocumentoRepository
from src.inscripcion.application.inscripcion_por_pasos import legajo_por_token
from src.inscripcion.domain.repo import LegajoRepository
from src.oferta_academica.domain.entities import ReglaDeNegocioViolada

LARGO_MAXIMO_NOMBRE = 255


class DocumentoDaniado(Exception):
    """El archivo en disco no coincide con el checksum guardado al subirlo."""


def _tipo_desde_texto(tipo: str) -> TipoDocumento:
    try:
        return TipoDocumento(tipo)
    except ValueError:
        validos = ", ".join(t.value for t in TipoDocumento)
        raise ArchivoInvalido(f"Tipo de documento desconocido: '{tipo}'. Válidos: {validos}")


def _limpiar_nombre(nombre_original: str) -> str:
    """Solo el nombre del archivo (sin carpetas), para mostrarlo al usuario."""
    nombre = os.path.basename((nombre_original or "").replace("\\", "/")).strip()
    return (nombre or "documento.pdf")[:LARGO_MAXIMO_NOMBRE]


async def subir_documento(
        token: str,
        tipo: str,
        nombre_original: str,
        contenido: bytes,
        repo_legajos: LegajoRepository,
        repo_documentos: DocumentoRepository,
        almacenamiento: AlmacenamientoArchivos,
) -> Documento:
    """Guarda un PDF del aspirante. Si ya había uno del mismo tipo, lo reemplaza."""
    legajo = await legajo_por_token(token, repo_legajos)
    if not legajo.puede_editar_formulario():
        raise ReglaDeNegocioViolada(
            f"No se pueden cambiar los documentos con el legajo en estado {legajo.estado.value}"
        )
    tipo_documento = _tipo_desde_texto(tipo)
    nombre = _limpiar_nombre(nombre_original)
    validar_pdf(contenido, nombre)

    documento_id = str(uuid.uuid4())
    # Nombre en disco: siempre un UUID (ARQUITECTURA.md §9.1)
    ruta = f"uploads/{legajo.cohorte_id}/{legajo.id}/{documento_id}.pdf"
    almacenamiento.guardar(ruta, contenido)

    anterior = await repo_documentos.obtener_por_tipo(legajo.id, tipo_documento)
    if anterior:
        await repo_documentos.eliminar(anterior.id)

    documento = await repo_documentos.guardar(
        Documento(
            id=documento_id,
            legajo_id=legajo.id,
            tipo=tipo_documento,
            nombre_original=nombre,
            ruta=ruta,
            checksum_sha256=calcular_checksum(contenido),
            tamanio_bytes=len(contenido),
            fecha_subida=datetime.now(),
        )
    )
    if anterior:
        almacenamiento.eliminar(anterior.ruta)
    return documento


async def eliminar_documento(
        token: str,
        documento_id: str,
        repo_legajos: LegajoRepository,
        repo_documentos: DocumentoRepository,
        almacenamiento: AlmacenamientoArchivos,
) -> None:
    legajo = await legajo_por_token(token, repo_legajos)
    documento = await repo_documentos.obtener(documento_id)
    # Un documento de otro legajo se trata igual que uno inexistente
    if documento is None or documento.legajo_id != legajo.id:
        raise DocumentoNoEncontrado()
    if not legajo.puede_editar_formulario():
        raise ReglaDeNegocioViolada(
            f"No se pueden cambiar los documentos con el legajo en estado {legajo.estado.value}"
        )
    await repo_documentos.eliminar(documento.id)
    almacenamiento.eliminar(documento.ruta)


def _leer_verificado(documento: Documento, almacenamiento: AlmacenamientoArchivos) -> bytes:
    contenido = almacenamiento.leer(documento.ruta)
    if calcular_checksum(contenido) != documento.checksum_sha256:
        raise DocumentoDaniado(f"El archivo '{documento.nombre_original}' no coincide con su checksum")
    return contenido


async def descargar_documento_del_tramite(
        token: str,
        documento_id: str,
        repo_legajos: LegajoRepository,
        repo_documentos: DocumentoRepository,
        almacenamiento: AlmacenamientoArchivos,
) -> tuple[Documento, bytes]:
    """El aspirante descarga uno de sus propios documentos."""
    legajo = await legajo_por_token(token, repo_legajos)
    documento = await repo_documentos.obtener(documento_id)
    if documento is None or documento.legajo_id != legajo.id:
        raise DocumentoNoEncontrado()
    return documento, _leer_verificado(documento, almacenamiento)


async def descargar_documento(
        documento_id: str, repo_documentos: DocumentoRepository, almacenamiento: AlmacenamientoArchivos
) -> tuple[Documento, bytes]:
    """La conducción descarga cualquier documento (el permiso lo controla el router)."""
    documento = await repo_documentos.obtener(documento_id)
    if documento is None:
        raise DocumentoNoEncontrado()
    return documento, _leer_verificado(documento, almacenamiento)