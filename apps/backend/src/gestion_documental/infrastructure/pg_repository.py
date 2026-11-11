import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.gestion_documental.domain.entities import Documento, TipoDocumento
from src.gestion_documental.domain.repo import DocumentoRepository
from src.gestion_documental.infrastructure.orm_models import DocumentoModel


def _a_uuid(valor) -> Optional[uuid.UUID]:
    """Convierte un id a UUID. Devuelve None si el texto no es un UUID válido."""
    if isinstance(valor, uuid.UUID):
        return valor
    try:
        return uuid.UUID(str(valor))
    except ValueError:
        return None


def _a_dominio(modelo: DocumentoModel) -> Documento:
    return Documento(
        id=str(modelo.id),
        legajo_id=str(modelo.legajo_id),
        tipo=TipoDocumento(modelo.tipo),
        nombre_original=modelo.nombre_original,
        ruta=modelo.path_storage,
        checksum_sha256=modelo.checksum_sha256,
        tamanio_bytes=modelo.tamanio_bytes or 0,
        fecha_subida=modelo.fecha_subida,
    )


class PostgresDocumentoRepository(DocumentoRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def listar_por_legajo(self, legajo_id: str) -> list[Documento]:
        resultado = await self._session.execute(
            select(DocumentoModel)
            .where(DocumentoModel.legajo_id == _a_uuid(legajo_id))
            .order_by(DocumentoModel.fecha_subida)
        )
        return [_a_dominio(m) for m in resultado.scalars().all()]

    async def obtener(self, documento_id: str) -> Optional[Documento]:
        id_uuid = _a_uuid(documento_id)
        if id_uuid is None:
            return None
        modelo = await self._session.get(DocumentoModel, id_uuid)
        return _a_dominio(modelo) if modelo else None

    async def obtener_por_tipo(self, legajo_id: str, tipo: TipoDocumento) -> Optional[Documento]:
        resultado = await self._session.execute(
            select(DocumentoModel)
            .where(DocumentoModel.legajo_id == _a_uuid(legajo_id))
            .where(DocumentoModel.tipo == tipo.value)
        )
        modelo = resultado.scalars().first()
        return _a_dominio(modelo) if modelo else None

    async def guardar(self, documento: Documento) -> Documento:
        modelo = DocumentoModel(
            id=_a_uuid(documento.id),
            legajo_id=_a_uuid(documento.legajo_id),
            tipo=documento.tipo.value,
            path_storage=documento.ruta,
            nombre_original=documento.nombre_original,
            checksum_sha256=documento.checksum_sha256,
            tamanio_bytes=documento.tamanio_bytes,
            fecha_subida=documento.fecha_subida,
        )
        self._session.add(modelo)
        await self._session.flush()
        return _a_dominio(modelo)

    async def eliminar(self, documento_id: str) -> None:
        await self._session.execute(delete(DocumentoModel).where(DocumentoModel.id == _a_uuid(documento_id)))
        await self._session.flush()