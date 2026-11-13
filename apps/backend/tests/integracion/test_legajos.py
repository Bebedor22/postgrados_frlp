"""Bandeja y workflow de la coordinación (RF-CORE-003, RF-CORE-004, BR-005)."""
import io
from datetime import datetime, timedelta

from openpyxl import load_workbook
from sqlalchemy import text

from src.shared.database.connection import engine


async def accion(cliente, cabeceras, legajo_id, nombre, cuerpo=None, rol="COORDINADOR"):
    return await cliente.post(f"/legajos/{legajo_id}/{nombre}", json=cuerpo, headers=cabeceras[rol])


async def test_workflow_completo(cliente, cabeceras, inscribir, emails):
    token, legajo_id = await inscribir()

    assert (await accion(cliente, cabeceras, legajo_id, "revisar")).json()["estado"] == "EN_REVISION"
    r = await accion(cliente, cabeceras, legajo_id, "observar", {"comentario": "Falta el título legalizado"})
    assert r.json()["estado"] == "OBSERVADO"
    # SRS: el email de la observación lleva el texto del comentario
    assert any("Falta el título legalizado" in e.cuerpo for e in emails)

    # El aspirante corrige y reenvía
    assert (await cliente.patch(f"/inscripciones/{token}", json={"ciudad": "Berisso"})).status_code == 200
    assert (await cliente.post(f"/inscripciones/{token}/confirmar")).json()["estado"] == "PENDIENTE"

    await accion(cliente, cabeceras, legajo_id, "revisar")
    aprobado = (await accion(cliente, cabeceras, legajo_id, "aprobar")).json()
    assert aprobado == {"legajo_id": legajo_id, "numero_legajo": "27-001-001", "estado": "COMPLETADO"}
    detalle = (await cliente.get(f"/legajos/{legajo_id}", headers=cabeceras["COORDINADOR"])).json()
    assert detalle["reserva_vence_el"] == (datetime.now().date() + timedelta(days=30)).isoformat()

    assert (await accion(cliente, cabeceras, legajo_id, "matricular")).json()["estado"] == "ACTIVO"
    historial = (await cliente.get(f"/inscripciones/{token}")).json()["historial"]
    assert [h["estado_nuevo"] for h in historial] == [
        "BORRADOR", "PENDIENTE", "EN_REVISION", "OBSERVADO", "PENDIENTE", "EN_REVISION", "COMPLETADO", "ACTIVO"]
    assert {"Tu inscripción fue aprobada", "¡Bienvenido/a al posgrado!"} <= {e.asunto for e in emails}


async def test_numeros_de_legajo_correlativos_por_cohorte(cliente, cabeceras, inscribir):
    numeros = []
    for dni in ["30000001", "30000002"]:
        _, legajo_id = await inscribir(dni=dni)
        await accion(cliente, cabeceras, legajo_id, "revisar")
        numeros.append((await accion(cliente, cabeceras, legajo_id, "aprobar")).json()["numero_legajo"])
    assert numeros == ["27-001-001", "27-001-002"]


async def test_transicion_invalida_da_409_y_no_manda_emails(cliente, cabeceras, inscribir, emails):
    _, legajo_id = await inscribir()
    emails.clear()
    r = await accion(cliente, cabeceras, legajo_id, "aprobar")  # Sin revisar
    assert r.status_code == 409 and r.json()["detail"] == "No se puede pasar de PENDIENTE a COMPLETADO"
    assert (await accion(cliente, cabeceras, legajo_id, "matricular")).status_code == 409
    assert emails == []


async def test_rechazo_y_baja_piden_motivo(cliente, cabeceras, inscribir):
    _, legajo_id = await inscribir()
    await accion(cliente, cabeceras, legajo_id, "revisar")
    assert (await accion(cliente, cabeceras, legajo_id, "rechazar", {"motivo": "corto"})).status_code == 422
    assert (await accion(cliente, cabeceras, legajo_id, "observar", {"comentario": "corto"})).status_code == 422
    r = await accion(cliente, cabeceras, legajo_id, "rechazar", {"motivo": "No cumple con el título requerido"})
    assert r.json()["estado"] == "RECHAZADO"
    # RECHAZADO es terminal
    assert (await accion(cliente, cabeceras, legajo_id, "baja", {"motivo": "Pidió la baja del legajo"})).status_code == 409


async def test_baja_de_un_estudiante_activo(cliente, cabeceras, inscribir, emails):
    _, legajo_id = await inscribir()
    for paso in ["revisar", "aprobar", "matricular"]:
        await accion(cliente, cabeceras, legajo_id, paso)
    r = await accion(cliente, cabeceras, legajo_id, "baja", {"motivo": "Pidió la baja por mudanza"})
    assert r.json()["estado"] == "BAJA"
    assert any(e.asunto == "Baja de tu legajo" for e in emails)


async def test_direccion_ve_pero_no_modifica(cliente, cabeceras, inscribir):
    _, legajo_id = await inscribir()
    assert (await cliente.get(f"/legajos/{legajo_id}", headers=cabeceras["DIRECCION"])).status_code == 200
    assert (await accion(cliente, cabeceras, legajo_id, "revisar", rol="DIRECCION")).status_code == 403


async def test_legajo_inexistente(cliente, cabeceras):
    r = await cliente.get("/legajos/00000000-0000-0000-0000-000000000000", headers=cabeceras["COORDINADOR"])
    assert r.status_code == 404


async def test_bandeja_filtros_y_resumen(cliente, cabeceras, inscribir, oferta):
    """RF-CORE-004: filtros combinados por estado, cohorte, carrera y beca, y búsqueda."""
    coord = cabeceras["COORDINADOR"]
    await inscribir(dni="30000001", carrera=0)
    await inscribir(dni="30000002", carrera=1, solicita_beca=True, tipo_beca="30", documentos=False, enviar=False)
    await inscribir(dni="30000003", carrera=1, completar=False, documentos=False, enviar=False)

    async def total(**filtros):
        r = await cliente.get("/legajos/", params={"cohorte_id": oferta["cohorte"], **filtros}, headers=coord)
        return r.json()["total"]

    assert await total() == 3
    assert await total(estado="PENDIENTE") == 1
    assert await total(carrera_id=oferta["carreras"][1]) == 2
    assert await total(tiene_beca="true") == 1
    assert await total(tiene_beca="false", carrera_id=oferta["carreras"][1]) == 1
    assert await total(buscar="30000003") == 1
    assert await total(buscar="rodrí") == 3  # Apellido parcial, sin importar mayúsculas
    resumen = (await cliente.get("/legajos/resumen", params={"cohorte_id": oferta["cohorte"]}, headers=coord)).json()
    assert resumen["PENDIENTE"] == 1 and resumen["BORRADOR"] == 2 and resumen["ACTIVO"] == 0


async def test_exportar_excel(cliente, cabeceras, inscribir):
    await inscribir(dni="30000001")
    await inscribir(dni="30000002", carrera=1, completar=False, documentos=False, enviar=False)
    r = await cliente.get("/legajos/exportar", params={"estado": "PENDIENTE"}, headers=cabeceras["DIRECCION"])
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    filas = list(load_workbook(io.BytesIO(r.content)).active.iter_rows(values_only=True))
    assert filas[0] == ("Nº Legajo", "Apellido y nombre", "DNI", "Estado", "Carrera", "Fecha inscripción")
    assert len(filas) == 2 and filas[1][2] == "30000001" and filas[1][3] == "Pendiente"
    assert (await cliente.get("/legajos/exportar")).status_code == 401


async def test_vencimiento_de_reservas(cliente, cabeceras, inscribir, emails):
    """BR-005: a los 30 días de aprobado sin matricularse, el legajo vence."""
    _, viejo = await inscribir(dni="30000001")
    _, nuevo = await inscribir(dni="30000002")
    for legajo_id in (viejo, nuevo):
        await accion(cliente, cabeceras, legajo_id, "revisar")
        await accion(cliente, cabeceras, legajo_id, "aprobar")
    # Se "envejece" la aprobación del primero: 31 días
    async with engine.begin() as conexion:
        await conexion.execute(
            text("UPDATE auditoria_legajos SET created_at = now() - interval '31 days' "
                 "WHERE legajo_id = :id AND estado_nuevo = 'COMPLETADO'"),
            {"id": viejo},
        )
    r = await cliente.post("/legajos/vencer-reservas", headers=cabeceras["COORDINADOR"])
    assert r.json()["cantidad"] == 1 and r.json()["legajos"][0]["legajo_id"] == viejo
    estado = lambda l: cliente.get(f"/legajos/{l}", headers=cabeceras["COORDINADOR"])
    assert (await estado(viejo)).json()["estado"] == "VENCIDO"
    assert (await estado(nuevo)).json()["estado"] == "COMPLETADO"
    assert any(e.destinatario == "coordinacion@posgrado.frlp.utn.edu.ar" for e in emails)


async def test_tarea_programada_de_vencimientos(cliente, cabeceras, inscribir, emails):
    """La misma regla, corrida por la tarea diaria (sin usuario: queda como automática)."""
    from src.inscripcion.infrastructure.tareas_programadas import ejecutar_vencimiento_de_reservas

    token, legajo_id = await inscribir()
    await accion(cliente, cabeceras, legajo_id, "revisar")
    await accion(cliente, cabeceras, legajo_id, "aprobar")
    async with engine.begin() as conexion:
        await conexion.execute(text("UPDATE auditoria_legajos SET created_at = now() - interval '40 days' "
                                    "WHERE estado_nuevo = 'COMPLETADO'"))
    assert await ejecutar_vencimiento_de_reservas() == 1
    ultimo = (await cliente.get(f"/inscripciones/{token}")).json()["historial"][-1]
    assert ultimo["estado_nuevo"] == "VENCIDO"
    assert await ejecutar_vencimiento_de_reservas() == 0  # No vuelve a vencer lo ya vencido