"""API del Módulo D: dashboard, filtro por tipo de carrera y exportación a Excel."""


async def legajo_activo(cliente, cabeceras, inscribir, **kwargs):
    _token, legajo_id = await inscribir(**kwargs)
    for accion in ("revisar", "aprobar", "matricular"):
        r = await cliente.post(f"/legajos/{legajo_id}/{accion}", headers=cabeceras["COORDINADOR"])
        assert r.status_code == 200, r.text
    return legajo_id


async def test_dashboard_y_filtro_por_tipo_de_carrera(cliente, cabeceras, oferta, inscribir):
    # Un activo en Maestría (carrera 0) y otro en Especialización (carrera 1)
    await legajo_activo(cliente, cabeceras, inscribir, dni="31000001", carrera=0)
    await legajo_activo(cliente, cabeceras, inscribir, dni="31000002", carrera=1)

    r = await cliente.get("/analytics/dashboard", headers=cabeceras["DIRECCION"])
    assert r.status_code == 200, r.text
    total = r.json()["total_inscriptos"]
    assert total >= 2
    assert set(r.json()["por_tipo_carrera"]) >= {"Maestria", "Especializacion"}

    r = await cliente.get("/analytics/dashboard?tipo_carrera=Maestria", headers=cabeceras["COORDINADOR"])
    assert r.status_code == 200, r.text
    assert set(r.json()["por_tipo_carrera"]) == {"Maestria"}
    assert r.json()["total_inscriptos"] < total

    # Valor inválido y rol sin permiso
    assert (await cliente.get("/analytics/dashboard?tipo_carrera=Otra", headers=cabeceras["DIRECCION"])).status_code == 422
    assert (await cliente.get("/analytics/dashboard", headers=cabeceras["CPR"])).status_code == 403


async def test_exportar_dashboard_es_excel_con_filtros(cliente, cabeceras, oferta):
    r = await cliente.get("/analytics/exportar?tipo_carrera=Doctorado", headers=cabeceras["DIRECCION"])
    assert r.status_code == 200, r.text
    assert "spreadsheetml" in r.headers["content-type"]
    assert r.content[:2] == b"PK"
