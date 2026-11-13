"""Esquemas Pydantic de los documentos del legajo."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.gestion_documental.domain.entities import Documento, RequisitoDocumental


class DocumentoResponse(BaseModel):
    id: str
    tipo: str
    descripcion: str
    nombre_original: str
    tamanio_bytes: int
    checksum_sha256: str = Field(description="SHA-256 del archivo, para verificar su integridad")
    fecha_subida: Optional[datetime]


class RequisitoDocumentalResponse(BaseModel):
    tipo: str
    descripcion: str
    obligatorio: bool
    presentado: bool
    documento: Optional[DocumentoResponse] = None


def documento_a_respuesta(documento: Documento) -> DocumentoResponse:
    return DocumentoResponse(
        id=documento.id,
        tipo=documento.tipo.value,
        descripcion=documento.tipo.descripcion,
        nombre_original=documento.nombre_original,
        tamanio_bytes=documento.tamanio_bytes,
        checksum_sha256=documento.checksum_sha256,
        fecha_subida=documento.fecha_subida,
    )


def requisito_a_respuesta(requisito: RequisitoDocumental) -> RequisitoDocumentalResponse:
    return RequisitoDocumentalResponse(
        tipo=requisito.tipo.value,
        descripcion=requisito.tipo.descripcion,
        obligatorio=requisito.obligatorio,
        presentado=requisito.presentado,
        documento=documento_a_respuesta(requisito.documento) if requisito.documento else None,
    )