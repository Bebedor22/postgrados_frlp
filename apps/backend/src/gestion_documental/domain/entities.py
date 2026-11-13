"""Documentos del legajo (dominio puro, sin frameworks).

Reglas del SRS (RF-CORE-002) y de ARQUITECTURA.md §9:
- Solo se aceptan PDF de hasta 5 MB. El tipo se controla con el contenido real del
  archivo (empieza con "%PDF-"), no con la extensión ni con lo que diga el navegador.
- Cada archivo se guarda con un nombre UUID; el nombre original solo se muestra.
- Se registra el checksum SHA-256 para poder verificar la integridad del archivo.
- Hay documentos obligatorios para enviar la inscripción.
"""
import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

TAMANIO_MAXIMO_MB = 5
TAMANIO_MAXIMO_BYTES = TAMANIO_MAXIMO_MB * 1024 * 1024
FIRMA_PDF = b"%PDF-"  # Los primeros bytes de todo archivo PDF


class TipoDocumento(Enum):
    FORM_INSCRIPCION = "FORM_INSCRIPCION"
    DNI = "DNI"
    TITULO_GRADO = "TITULO_GRADO"
    PARTIDA = "PARTIDA"
    CUIT_CUIL = "CUIT_CUIL"
    TITULO_POSGRADO = "TITULO_POSGRADO"
    FORM_BECA = "FORM_BECA"

    @property
    def descripcion(self) -> str:
        return DESCRIPCIONES[self]


DESCRIPCIONES = {
    TipoDocumento.FORM_INSCRIPCION: "Formulario de preinscripción firmado",
    TipoDocumento.DNI: "Copia del DNI o pasaporte",
    TipoDocumento.TITULO_GRADO: "Copia del título de grado",
    TipoDocumento.PARTIDA: "Partida de nacimiento",
    TipoDocumento.CUIT_CUIL: "Constancia de CUIT/CUIL",
    TipoDocumento.TITULO_POSGRADO: "Título de posgrado",
    TipoDocumento.FORM_BECA: "Formulario de beca firmado",
}


class ArchivoInvalido(ValueError):
    """El archivo no cumple las reglas (no es PDF, está vacío o es muy grande)."""


class DocumentoNoEncontrado(Exception):
    pass


@dataclass
class Documento:
    id: str
    legajo_id: str
    tipo: TipoDocumento
    nombre_original: str
    ruta: str  # Ruta interna relativa al storage: nunca se expone en la API
    checksum_sha256: str
    tamanio_bytes: int
    fecha_subida: Optional[datetime] = None


@dataclass
class RequisitoDocumental:
    """Un documento que el aspirante tiene que (o puede) presentar."""

    tipo: TipoDocumento
    obligatorio: bool
    documento: Optional[Documento] = None

    @property
    def presentado(self) -> bool:
        return self.documento is not None


def validar_pdf(contenido: bytes, nombre_original: str) -> None:
    """Rechaza archivos vacíos, de más de 5 MB o que no sean PDF de verdad."""
    if not contenido:
        raise ArchivoInvalido(f"El archivo '{nombre_original}' está vacío")
    if len(contenido) > TAMANIO_MAXIMO_BYTES:
        raise ArchivoInvalido(
            f"El archivo es demasiado grande. Máximo permitido: {TAMANIO_MAXIMO_MB}MB"
        )
    if not contenido.startswith(FIRMA_PDF):
        raise ArchivoInvalido("Solo se aceptan archivos en formato PDF")


def calcular_checksum(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()


def requisitos_documentales(
        solicita_beca: bool, tiene_titulo_posgrado: bool, presentados: list[Documento]
) -> list[RequisitoDocumental]:
    """Lista de documentos del legajo según el SRS (RF-CORE-002).

    Obligatorios para todos: formulario de preinscripción, DNI, título de grado,
    partida de nacimiento y CUIT/CUIL. El título de posgrado es obligatorio solo si
    el aspirante declaró uno, y el formulario de beca solo si solicita beca.
    """
    por_tipo = {doc.tipo: doc for doc in presentados}
    obligatorios = {
        TipoDocumento.FORM_INSCRIPCION: True,
        TipoDocumento.DNI: True,
        TipoDocumento.TITULO_GRADO: True,
        TipoDocumento.PARTIDA: True,
        TipoDocumento.CUIT_CUIL: True,
        TipoDocumento.TITULO_POSGRADO: tiene_titulo_posgrado,
        TipoDocumento.FORM_BECA: solicita_beca,
    }
    requisitos = []
    for tipo, obligatorio in obligatorios.items():
        # El formulario de beca solo aparece si pidió beca (o si ya lo había subido)
        if tipo == TipoDocumento.FORM_BECA and not solicita_beca and tipo not in por_tipo:
            continue
        requisitos.append(RequisitoDocumental(tipo, obligatorio, por_tipo.get(tipo)))
    return requisitos


def documentos_faltantes(requisitos: list[RequisitoDocumental]) -> list[TipoDocumento]:
    return [r.tipo for r in requisitos if r.obligatorio and not r.presentado]