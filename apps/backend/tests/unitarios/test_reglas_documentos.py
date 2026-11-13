"""Reglas de los documentos PDF (SRS RF-CORE-002)."""
import pytest

from src.gestion_documental.domain.entities import (
    TAMANIO_MAXIMO_BYTES,
    ArchivoInvalido,
    Documento,
    TipoDocumento,
    calcular_checksum,
    documentos_faltantes,
    requisitos_documentales,
    validar_pdf,
)
from src.gestion_documental.infrastructure.file_storage import AlmacenamientoLocal

T = TipoDocumento
PDF = b"%PDF-1.4\n contenido de prueba"
OBLIGATORIOS = [T.FORM_INSCRIPCION, T.DNI, T.TITULO_GRADO, T.PARTIDA, T.CUIT_CUIL]


def documento(tipo: TipoDocumento) -> Documento:
    return Documento("id-" + tipo.value, "legajo", tipo, f"{tipo.value}.pdf", "ruta", "abc", 10)


def test_pdf_valido():
    validar_pdf(PDF, "titulo.pdf")


@pytest.mark.parametrize("contenido, mensaje", [
    (b"", "vacío"),
    (b"\xff\xd8\xff\xe0 una foto", "Solo se aceptan archivos en formato PDF"),
    (b"MZ un ejecutable renombrado a .pdf", "Solo se aceptan archivos en formato PDF"),
    (b"%PDF-" + b"0" * TAMANIO_MAXIMO_BYTES, "Máximo permitido: 5MB"),
])
def test_archivos_rechazados(contenido, mensaje):
    with pytest.raises(ArchivoInvalido, match=mensaje):
        validar_pdf(contenido, "archivo.pdf")


def test_checksum_sha256():
    assert calcular_checksum(b"hola") == "b221d9dbb083a7f33428d7c2a3c3198ae925614d70210e28716ccaa7cd4ddb79"


def test_requisitos_basicos():
    requisitos = requisitos_documentales(solicita_beca=False, tiene_titulo_posgrado=False, presentados=[])
    obligatorios = [r.tipo for r in requisitos if r.obligatorio]
    assert obligatorios == OBLIGATORIOS
    assert T.FORM_BECA not in [r.tipo for r in requisitos]  # Sin beca no aparece
    assert documentos_faltantes(requisitos) == OBLIGATORIOS


def test_beca_y_titulo_de_posgrado_se_vuelven_obligatorios():
    requisitos = requisitos_documentales(solicita_beca=True, tiene_titulo_posgrado=True, presentados=[])
    faltan = documentos_faltantes(requisitos)
    assert T.FORM_BECA in faltan and T.TITULO_POSGRADO in faltan


def test_con_todos_los_obligatorios_no_falta_nada():
    presentados = [documento(t) for t in OBLIGATORIOS]
    requisitos = requisitos_documentales(solicita_beca=False, tiene_titulo_posgrado=False, presentados=presentados)
    assert documentos_faltantes(requisitos) == []
    assert all(r.presentado for r in requisitos if r.obligatorio)


def test_formulario_de_beca_subido_sigue_apareciendo_si_desmarca_la_beca():
    requisitos = requisitos_documentales(False, False, [documento(T.FORM_BECA)])
    beca = next(r for r in requisitos if r.tipo == T.FORM_BECA)
    assert beca.presentado and not beca.obligatorio


def test_almacenamiento_local(tmp_path):
    almacenamiento = AlmacenamientoLocal(str(tmp_path))
    almacenamiento.guardar("uploads/c/l/archivo.pdf", PDF)
    assert almacenamiento.leer("uploads/c/l/archivo.pdf") == PDF
    almacenamiento.eliminar("uploads/c/l/archivo.pdf")
    almacenamiento.eliminar("uploads/c/l/archivo.pdf")  # Borrar dos veces no falla
    with pytest.raises(FileNotFoundError):
        almacenamiento.leer("uploads/c/l/archivo.pdf")


def test_almacenamiento_no_sale_de_su_carpeta(tmp_path):
    almacenamiento = AlmacenamientoLocal(str(tmp_path / "storage"))
    with pytest.raises(ValueError, match="fuera del almacenamiento"):
        almacenamiento.leer("../../etc/passwd")