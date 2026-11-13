"""Almacenamiento de los PDFs en disco (ARQUITECTURA.md §9).

La carpeta base es STORAGE_PATH (en Docker, el volumen /var/postgrado-storage).
Ningún servidor web la publica: los archivos solo salen por los endpoints de
descarga, que controlan permisos.
"""
from pathlib import Path

from src.gestion_documental.domain.repo import AlmacenamientoArchivos


class AlmacenamientoLocal(AlmacenamientoArchivos):
    def __init__(self, carpeta_base: str):
        self._base = Path(carpeta_base).resolve()

    def _ruta_segura(self, ruta: str) -> Path:
        """Ruta absoluta dentro de la carpeta base (evita rutas tipo '../../etc')."""
        destino = (self._base / ruta).resolve()
        if not destino.is_relative_to(self._base):
            raise ValueError("Ruta fuera del almacenamiento")
        return destino

    def guardar(self, ruta: str, contenido: bytes) -> None:
        destino = self._ruta_segura(ruta)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)

    def leer(self, ruta: str) -> bytes:
        return self._ruta_segura(ruta).read_bytes()

    def eliminar(self, ruta: str) -> None:
        self._ruta_segura(ruta).unlink(missing_ok=True)