"""Contratos que la capa de aplicación necesita (las implementaciones viven en infrastructure/)."""
from typing import Optional

from .entities import Documento, TipoDocumento


class DocumentoRepository:
    """Guarda y busca los datos de los documentos (no el archivo)."""

    async def listar_por_legajo(self, legajo_id: str) -> list[Documento]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener(self, documento_id: str) -> Optional[Documento]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener_por_tipo(self, legajo_id: str, tipo: TipoDocumento) -> Optional[Documento]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def guardar(self, documento: Documento) -> Documento:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def eliminar(self, documento_id: str) -> None:
        raise NotImplementedError("Implementar en pg_repository.py")


class AlmacenamientoArchivos:
    """Lee y escribe el contenido de los archivos (disco, nube, etc.)."""

    def guardar(self, ruta: str, contenido: bytes) -> None:
        raise NotImplementedError("Implementar en file_storage.py")

    def leer(self, ruta: str) -> bytes:
        raise NotImplementedError("Implementar en file_storage.py")

    def eliminar(self, ruta: str) -> None:
        raise NotImplementedError("Implementar en file_storage.py")