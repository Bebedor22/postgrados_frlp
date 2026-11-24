"""API del Módulo C: TFI/Tesis, semáforo, riesgo, exportación y permisos (BR-004/BR-008)."""
from datetime import date, timedelta

from sqlalchemy import text

from src.shared.database.connection import engine


async def legajo_activo(cliente, cabeceras, inscribir, **kwargs):
    token, legajo_id = await inscribir(**kwargs)
    for accion in ("revisar", "aprobar", "matricular"):
        r = await cliente.post(f"/legajos/{legajo_id}/{accion}", headers=cabeceras["COORDINADOR"])
        assert r.status_code == 200, r.text
    return token, legajo_id


async def crear_seminario(cliente, cabeceras, carrera_id, codigo="SEM-C1"):
    r = await cliente.post(
        "/seminarios/",
        json={
            "carrera_id": carrera_id, "nombre": "Metodología", "codigo": codigo,
            "horas_catedra": 32, "es_obligatorio": True, "docente_email": "docente@fenix.test",
        },
        headers=cabeceras["COORDINADOR"],
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_registro_y_edicion_de_tfi_solo_cpr(cliente, cabeceras, oferta, inscribir):
    _token, legajo_id = await legajo_activo(cliente, cabeceras, inscribir)
    datos = {
        "tipo": "TFI", "titulo": "Trabajo final de prueba",
        "director_nombre": "Ana Vega", "director_email": "ana@frlp.utn.edu.ar",
        "codirector_nombre": "Luis Ruiz", "numero_resolucion": "CPR-01",
    }
    # BR-004: conducción no puede cargar ni modificar
    assert (await cliente.post(f"/legajos/{legajo_id}/trabajo-final", json=datos,
                               headers=cabeceras["COORDINADOR"])).status_code == 403

    r = await cliente.post(f"/legajos/{legajo_id}/trabajo-final", json=datos, headers=cabeceras["CPR"])
    assert r.status_code == 201, r.text
    trabajo = r.json()
    assert trabajo["tipo"] == "TFI" and trabajo["fecha_aprobacion_cpr"] is None

    # Dirección sí puede leer
    r = await cliente.get(f"/legajos/{legajo_id}/trabajo-final", headers=cabeceras["DIRECCION"])
    assert r.status_code == 200 and r.json()["id"] == trabajo["id"]

    # Alta duplicada: se usa PATCH
    assert (await cliente.post(f"/legajos/{legajo_id}/trabajo-final", json=datos,
                               headers=cabeceras["CPR"])).status_code == 422

    fecha = date.today() - timedelta(days=10)
    r = await cliente.patch(
        f"/trabajos-finales/{trabajo['id']}",
        json={"fecha_aprobacion_cpr": fecha.isoformat(), "titulo": "Título corregido"},
        headers=cabeceras["CPR"],
    )
    assert r.status_code == 200, r.text
    assert r.json()["fecha_aprobacion_cpr"] == fecha.isoformat()

    # La fecha se puede quitar explícitamente
    r = await cliente.patch(
        f"/trabajos-finales/{trabajo['id']}", json={"limpiar_fecha_cpr": True},
        headers=cabeceras["CPR"],
    )
    assert r.status_code == 200 and r.json()["fecha_aprobacion_cpr"] is None

    assert (await cliente.patch(f"/trabajos-finales/{trabajo['id']}", json={},
                                headers=cabeceras["COORDINADOR"])).status_code == 403


async def test_tfi_con_cpr_y_seminarios_aprobados_gradua_automaticamente(
        cliente, cabeceras, oferta, inscribir
):
    _token, legajo_id = await legajo_activo(cliente, cabeceras, inscribir)
    seminario = await crear_seminario(cliente, cabeceras, oferta["carreras"][0])
    await cliente.post(
        f"/seminarios/{seminario['id']}/estudiantes",
        json={"legajo_id": legajo_id}, headers=cabeceras["COORDINADOR"],
    )
    await cliente.patch(
        f"/seminarios/{seminario['id']}/notas",
        json={"notas": [{"legajo_id": legajo_id, "nota": 9}]},
        headers=cabeceras["DOCENTE"],
    )

    r = await cliente.post(
        f"/legajos/{legajo_id}/trabajo-final",
        json={
            "tipo": "TESIS", "titulo": "Tesis de prueba",
            "director_nombre": "Ana Vega", "director_email": "ana@frlp.utn.edu.ar",
            "fecha_aprobacion_cpr": (date.today() - timedelta(days=5)).isoformat(),
        },
        headers=cabeceras["CPR"],
    )
    assert r.status_code == 201, r.text
    detalle = (await cliente.get(f"/legajos/{legajo_id}", headers=cabeceras["COORDINADOR"])).json()
    assert detalle["estado"] == "GRADUADO"


async def test_validaciones_de_tfi(cliente, cabeceras, oferta, inscribir):
    _token, legajo_id = await legajo_activo(cliente, cabeceras, inscribir)
    base = {
        "tipo": "TFI", "titulo": "Trabajo válido",
        "director_nombre": "Ana", "director_email": "ana@mail.com",
    }
    # fecha futura
    r = await cliente.post(
        f"/legajos/{legajo_id}/trabajo-final",
        json={**base, "fecha_aprobacion_cpr": (date.today() + timedelta(days=5)).isoformat()},
        headers=cabeceras["CPR"],
    )
    assert r.status_code == 422
    # legajo inexistente
    r = await cliente.post(
        "/legajos/00000000-0000-0000-0000-000000000000/trabajo-final",
        json=base, headers=cabeceras["CPR"],
    )
    assert r.status_code == 404
    # tipo inválido
    r = await cliente.post(
        f"/legajos/{legajo_id}/trabajo-final", json={**base, "tipo": "TESINA"},
        headers=cabeceras["CPR"],
    )
    assert r.status_code == 422


async def test_verde_manual_se_respeta_y_se_puede_restaurar(cliente, cabeceras, oferta, inscribir):
    _token, legajo_id = await legajo_activo(cliente, cabeceras, inscribir)

    r = await cliente.get(f"/legajos/{legajo_id}/semaforo", headers=cabeceras["COORDINADOR"])
    assert r.status_code == 200 and r.json()["semaforo"] == "VERDE"

    # Conducción puede leer el dashboard; Dirección también
    assert (await cliente.get("/graduacion/semaforo", headers=cabeceras["COORDINADOR"])).status_code == 200
    assert (await cliente.get("/graduacion/semaforo", headers=cabeceras["DIRECCION"])).status_code == 200
    assert (await cliente.get(f"/legajos/{legajo_id}/semaforo", headers=cabeceras["DIRECCION"])).status_code == 403

    r = await cliente.patch(
        f"/legajos/{legajo_id}/semaforo/verde", json={"manual": True},
        headers=cabeceras["COORDINADOR"],
    )
    assert r.status_code == 200 and r.json()["semaforo_manual"] is True

    # Un recálculo posterior no pisa el VERDE manual
    r = await cliente.get(f"/legajos/{legajo_id}/semaforo", headers=cabeceras["COORDINADOR"])
    assert r.json()["semaforo"] == "VERDE" and r.json()["semaforo_manual"] is True

    r = await cliente.patch(
        f"/legajos/{legajo_id}/semaforo/verde", json={"manual": False},
        headers=cabeceras["COORDINADOR"],
    )
    assert r.status_code == 200 and r.json()["semaforo_manual"] is False
    assert (await cliente.patch(f"/legajos/{legajo_id}/semaforo/verde", json={},
                                headers=cabeceras["CPR"])).status_code == 403


async def test_en_riesgo_y_exportacion(cliente, cabeceras, oferta, inscribir):
    _token, legajo_id = await legajo_activo(cliente, cabeceras, inscribir)
    # Sin aprobar el obligatorio y con la cursada envejecida → ROJO
    await crear_seminario(cliente, cabeceras, oferta["carreras"][0])
    async with engine.begin() as conexion:
        await conexion.execute(
            text("UPDATE legajos SET fecha_activacion = now() - interval '900 days' WHERE id = :id"),
            {"id": legajo_id},
        )
    r = await cliente.get(f"/legajos/{legajo_id}/semaforo", headers=cabeceras["COORDINADOR"])
    assert r.status_code == 200 and r.json()["semaforo"] == "ROJO"

    r = await cliente.get("/graduacion/en-riesgo", headers=cabeceras["COORDINADOR"])
    assert r.status_code == 200 and r.json()["total"] == 1
    assert r.json()["legajos"][0]["legajo_id"] == legajo_id
    # Alias deprecated
    assert (await cliente.get("/en-riesgo", headers=cabeceras["COORDINADOR"])).json()["total"] == 1

    r = await cliente.get("/graduacion/en-riesgo/exportar", headers=cabeceras["COORDINADOR"])
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    assert r.content[:2] == b"PK"
    assert (await cliente.get("/graduacion/en-riesgo", headers=cabeceras["CPR"])).status_code == 403


async def test_busqueda_de_legajos_para_tesis(cliente, cabeceras, oferta, inscribir):
    token, legajo_id = await legajo_activo(cliente, cabeceras, inscribir, apellido="Fernández")
    r = await cliente.get("/tesis/legajos?buscar=Fernández", headers=cabeceras["CPR"])
    assert r.status_code == 200, r.text
    assert any(f["legajo_id"] == legajo_id for f in r.json())
    assert "datos" not in r.json()[0]
    assert (await cliente.get("/tesis/legajos", headers=cabeceras["COORDINADOR"])).status_code == 403


DATOS_TFI = {
    "tipo": "TFI", "titulo": "Trabajo final de prueba",
    "director_nombre": "Ana Vega", "director_email": "ana@frlp.utn.edu.ar",
}


async def test_tfi_se_rechaza_si_el_legajo_no_esta_activo(cliente, cabeceras, oferta, inscribir):
    # PENDIENTE: inscripción confirmada, todavía sin revisar
    _t, pendiente = await inscribir(dni="30000001")
    r = await cliente.post(f"/legajos/{pendiente}/trabajo-final", json=DATOS_TFI, headers=cabeceras["CPR"])
    assert r.status_code == 422, r.text
    assert "ACTIVO" in r.json()["detail"]
    assert (await cliente.get(f"/legajos/{pendiente}/trabajo-final", headers=cabeceras["CPR"])).status_code == 404

    # RECHAZADO
    _t, rechazado = await inscribir(dni="30000002")
    assert (await cliente.post(f"/legajos/{rechazado}/revisar", headers=cabeceras["COORDINADOR"])).status_code == 200
    r = await cliente.post(
        f"/legajos/{rechazado}/rechazar", json={"motivo": "No cumple con el título requerido"},
        headers=cabeceras["COORDINADOR"],
    )
    assert r.status_code == 200, r.text
    r = await cliente.post(f"/legajos/{rechazado}/trabajo-final", json=DATOS_TFI, headers=cabeceras["CPR"])
    assert r.status_code == 422, r.text
    assert (await cliente.get(f"/legajos/{rechazado}/trabajo-final", headers=cabeceras["CPR"])).status_code == 404


async def test_portal_cpr_lista_solo_legajos_activos(cliente, cabeceras, oferta, inscribir):
    _t, pendiente = await inscribir(dni="30000001", apellido="Pendiente")
    _t, activo = await legajo_activo(cliente, cabeceras, inscribir, dni="30000003", apellido="Activo")

    r = await cliente.get("/tesis/legajos", headers=cabeceras["CPR"])
    assert r.status_code == 200, r.text
    ids = {f["legajo_id"] for f in r.json()}
    assert activo in ids
    assert pendiente not in ids
    assert all(f["estado"] == "ACTIVO" for f in r.json())
