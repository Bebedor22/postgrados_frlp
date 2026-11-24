"""Endpoints de los documentos del legajo (RF-CORE-002, ARQUITECTURA.md §9).

- `router_aspirante` (se monta en /api/v1/inscripciones): el aspirante sube, borra y
  descarga sus PDFs usando el token de su link personal.
- `router` (se monta en /api/v1/documentos): la conducción descarga los PDFs.

Los archivos nunca se publican por URL directa: siempre salen por estos endpoints.
"""
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.gestion_documental.application.gestionar_documentos import (
    DocumentoDaniado,
    descargar_documento,
    descargar_documento_del_tramite,
    eliminar_documento,
    subir_documento,
)
from src.gestion_documental.domain.entities import (
    TAMANIO_MAXIMO_BYTES,
    ArchivoInvalido,
    Documento,
    DocumentoNoEncontrado,
    TipoDocumento,
)
from src.gestion_documental.infrastructure.file_storage import AlmacenamientoLocal
from src.gestion_documental.infrastructure.pg_repository import PostgresDocumentoRepository
from src.gestion_documental.presentation.schemas import DocumentoResponse, documento_a_respuesta
from src.inscripcion.application.inscripcion_por_pasos import TramiteNoEncontrado
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.oferta_academica.domain.entities import ReglaDeNegocioViolada
from src.shared.auth.dependencies import require_role
from src.shared.config import get_settings
from src.shared.database.connection import get_db

router_aspirante = APIRouter()
router = APIRouter()


def get_almacenamiento() -> AlmacenamientoLocal:
    """Dependency: dónde se guardan los PDFs (STORAGE_PATH)."""
    return AlmacenamientoLocal(get_settings().storage_path)


def _error_http(error: Exception) -> HTTPException:
    if isinstance(error, TramiteNoEncontrado):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Trámite no encontrado: revisá el link")
    if isinstance(error, (DocumentoNoEncontrado, FileNotFoundError)):
        return HTTPException(status.HTTP_404_NOT_FOUND, "Documento no encontrado")
    if isinstance(error, ArchivoInvalido):
        return HTTPException(422, str(error))
    return HTTPException(status.HTTP_409_CONFLICT, str(error))  # Regla de negocio o archivo dañado


def _respuesta_pdf(documento: Documento, contenido: bytes) -> Response:
    """Entrega el PDF para verlo en el navegador (inline) con su nombre original."""
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(documento.nombre_original)}",
            "X-Checksum-SHA256": documento.checksum_sha256,
        },
    )


ERRORES = (TramiteNoEncontrado, DocumentoNoEncontrado, FileNotFoundError, ArchivoInvalido,
           ReglaDeNegocioViolada, DocumentoDaniado)


# ── Aspirante (con el token del link personal) ───────────────────────────────

@router_aspirante.post(
    "/{token}/documentos",
    response_model=DocumentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir un documento PDF",
    description=(
        "Solo PDF de hasta 5 MB (se controla el contenido real del archivo). Se guarda con nombre UUID "
        "y checksum SHA-256. Si ya había un documento de ese tipo, lo reemplaza. "
        "Solo con el legajo en BORRADOR u OBSERVADO."
    ),
)
async def api_subir_documento(
        token: str,
        tipo: TipoDocumento = Form(description="Tipo de documento"),
        archivo: UploadFile = File(description="Archivo PDF"),
        db: AsyncSession = Depends(get_db, scope="function"),
        almacenamiento: AlmacenamientoLocal = Depends(get_almacenamiento),
):
    # Se lee como máximo 1 byte más que el límite: alcanza para saber si se pasa
    contenido = await archivo.read(TAMANIO_MAXIMO_BYTES + 1)
    try:
        documento = await subir_documento(
            token, tipo.value, archivo.filename or "documento.pdf", contenido,
            PostgresLegajoRepository(db), PostgresDocumentoRepository(db), almacenamiento,
        )
    except ERRORES as e:
        raise _error_http(e)
    return documento_a_respuesta(documento)


@router_aspirante.delete(
    "/{token}/documentos/{documento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un documento propio",
    description="Solo con el legajo en BORRADOR u OBSERVADO.",
)
async def api_eliminar_documento(
        token: str,
        documento_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        almacenamiento: AlmacenamientoLocal = Depends(get_almacenamiento),
):
    try:
        await eliminar_documento(
            token, documento_id, PostgresLegajoRepository(db), PostgresDocumentoRepository(db), almacenamiento
        )
    except ERRORES as e:
        raise _error_http(e)


@router_aspirante.get(
    "/{token}/documentos/{documento_id}/descarga",
    summary="Ver un documento propio",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def api_descargar_documento_propio(
        token: str,
        documento_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        almacenamiento: AlmacenamientoLocal = Depends(get_almacenamiento),
):
    try:
        documento, contenido = await descargar_documento_del_tramite(
            token, documento_id, PostgresLegajoRepository(db), PostgresDocumentoRepository(db), almacenamiento
        )
    except ERRORES as e:
        raise _error_http(e)
    return _respuesta_pdf(documento, contenido)


# ── Conducción ───────────────────────────────────────────────────────────────

@router.get(
    "/{documento_id}/download",
    summary="Descargar un documento (conducción)",
    description="Para COORDINADOR y DIRECCION. Verifica el checksum antes de entregar el archivo.",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
async def api_descargar_documento(
        documento_id: str,
        db: AsyncSession = Depends(get_db, scope="function"),
        almacenamiento: AlmacenamientoLocal = Depends(get_almacenamiento),
        _usuario: dict = Depends(require_role("COORDINADOR", "DIRECCION")),
):
    try:
        documento, contenido = await descargar_documento(documento_id, PostgresDocumentoRepository(db), almacenamiento)
    except ERRORES as e:
        raise _error_http(e)
    return _respuesta_pdf(documento, contenido)