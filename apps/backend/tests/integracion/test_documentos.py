"""Documentos PDF del legajo (RF-CORE-002, ASR-001)."""
import os

from ayudas import PDF, subir
from src.shared.config import get_settings


async def test_requisitos_y_subida(cliente, inscribir):
    token, _ = await inscribir(documentos=False, enviar=False)
    tramite = (await cliente.get(f"/inscripciones/{token}")).json()
    assert [d["tipo"] for d in tramite["documentos"] if d["obligatorio"]] == [
        "FORM_INSCRIPCION", "DNI", "TITULO_GRADO", "PARTIDA", "CUIT_CUIL"]

    r = await subir(cliente, token, "DNI", nombre="C:\\Users\\ana\\mi dni.pdf")
    assert r.status_code == 201
    documento = r.json()
    assert documento["nombre_original"] == "mi dni.pdf"  # Sin la carpeta de la PC del aspirante
    assert documento["tamanio_bytes"] == len(PDF)
    assert len(documento["checksum_sha256"]) == 64

    # En el disco se guarda con un nombre UUID, nunca con el original
    archivos = [f for _, _, fs in os.walk(get_settings().storage_path) for f in fs]
    assert f"{documento['id']}.pdf" in archivos and "mi dni.pdf" not in archivos


async def test_archivos_invalidos(cliente, inscribir):
    token, _ = await inscribir(documentos=False, enviar=False)
    r = await subir(cliente, token, "DNI", contenido=b"\xff\xd8\xff una foto", nombre="dni.jpg", tipo_mime="image/jpeg")
    assert r.status_code == 422 and r.json()["detail"] == "Solo se aceptan archivos en formato PDF"
    r = await subir(cliente, token, "DNI", contenido=b"%PDF-" + b"0" * (5 * 1024 * 1024 + 1))
    assert r.status_code == 422 and "Máximo permitido: 5MB" in r.json()["detail"]
    assert (await subir(cliente, token, "FOTO_CARNET")).status_code == 422


async def test_no_se_envia_sin_los_documentos_obligatorios(cliente, inscribir):
    token, _ = await inscribir(documentos=False, enviar=False)
    await subir(cliente, token, "DNI")
    r = await cliente.post(f"/inscripciones/{token}/confirmar")
    assert r.status_code == 409
    assert "Faltan documentos" in r.json()["detail"] and "Partida de nacimiento" in r.json()["detail"]


async def test_reemplazar_y_borrar(cliente, inscribir):
    token, _ = await inscribir(documentos=False, enviar=False)
    viejo = (await subir(cliente, token, "DNI", nombre="viejo.pdf")).json()
    nuevo = (await subir(cliente, token, "DNI", nombre="nuevo.pdf")).json()
    dni = [d for d in (await cliente.get(f"/inscripciones/{token}")).json()["documentos"] if d["tipo"] == "DNI"][0]
    assert dni["documento"]["nombre_original"] == "nuevo.pdf"
    assert (await cliente.get(f"/inscripciones/{token}/documentos/{viejo['id']}/descarga")).status_code == 404

    assert (await cliente.delete(f"/inscripciones/{token}/documentos/{nuevo['id']}")).status_code == 204
    assert (await cliente.delete(f"/inscripciones/{token}/documentos/{nuevo['id']}")).status_code == 404


async def test_despues_de_enviar_no_se_cambian_los_documentos(cliente, inscribir):
    token, _ = await inscribir()
    documento = (await cliente.get(f"/inscripciones/{token}")).json()["documentos"][0]["documento"]
    assert (await subir(cliente, token, "DNI")).status_code == 409
    assert (await cliente.delete(f"/inscripciones/{token}/documentos/{documento['id']}")).status_code == 409


async def test_permisos_de_descarga(cliente, inscribir, cabeceras):
    """Los PDFs solo salen por endpoint: el aspirante con su token, la conducción con JWT y rol."""
    token, legajo_id = await inscribir()
    otro_token, _ = await inscribir(dni="30111222", enviar=False, documentos=False)
    documento_id = (await cliente.get(f"/inscripciones/{token}")).json()["documentos"][0]["documento"]["id"]

    propio = await cliente.get(f"/inscripciones/{token}/documentos/{documento_id}/descarga")
    assert propio.status_code == 200 and propio.content.startswith(b"%PDF-")
    assert propio.headers["content-type"] == "application/pdf"
    # Con el link de otro aspirante no se puede ver
    assert (await cliente.get(f"/inscripciones/{otro_token}/documentos/{documento_id}/descarga")).status_code == 404

    ruta = f"/documentos/{documento_id}/download"
    assert (await cliente.get(ruta, headers=cabeceras["COORDINADOR"])).status_code == 200
    assert (await cliente.get(ruta, headers=cabeceras["DIRECCION"])).status_code == 200
    assert (await cliente.get(ruta, headers=cabeceras["DOCENTE"])).status_code == 403
    assert (await cliente.get(ruta)).status_code == 401
    assert (await cliente.get("/documentos/no-es-un-id/download", headers=cabeceras["COORDINADOR"])).status_code == 404

    # La conducción ve los documentos en el detalle del legajo
    detalle = (await cliente.get(f"/legajos/{legajo_id}", headers=cabeceras["COORDINADOR"])).json()
    assert sum(d["presentado"] for d in detalle["documentos"]) == 5


async def test_archivo_alterado_en_el_disco(cliente, inscribir, cabeceras):
    """Integridad: si el archivo no coincide con su checksum, no se entrega."""
    token, _ = await inscribir()
    documento_id = (await cliente.get(f"/inscripciones/{token}")).json()["documentos"][0]["documento"]["id"]
    for carpeta, _, archivos in os.walk(get_settings().storage_path):
        if f"{documento_id}.pdf" in archivos:
            with open(os.path.join(carpeta, f"{documento_id}.pdf"), "ab") as archivo:
                archivo.write(b"modificado")
    r = await cliente.get(f"/documentos/{documento_id}/download", headers=cabeceras["COORDINADOR"])
    assert r.status_code == 409 and "checksum" in r.json()["detail"]