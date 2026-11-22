"""API del Módulo B: alta de seminarios, inscripción de estudiantes y notas finales."""
DOCENTE = "docente@fenix.test"


async def _crear_seminario(cliente, cabeceras, carrera_id, **cambios):
    datos = {
        "carrera_id": carrera_id,
        "nombre": "Metodología de investigación",
        "codigo": "MET-01",
        "horas_catedra": 60,
        "docente_email": DOCENTE,
    }
    datos.update(cambios)
    r = await cliente.post("/seminarios/", json=datos, headers=cabeceras["COORDINADOR"])
    assert r.status_code == 201, r.text
    return r.json()


async def test_ciclo_completo_de_un_seminario(cliente, cabeceras, oferta, inscribir):
    """Crear → inscribir → cargar nota → ver el progreso que usa el semáforo."""
    coord = cabeceras["COORDINADOR"]
    seminario = await _crear_seminario(cliente, cabeceras, oferta["carreras"][0])
    _token, legajo_id = await inscribir()

    r = await cliente.post(
        f"/seminarios/{seminario['id']}/estudiantes", json={"legajo_id": legajo_id}, headers=coord
    )
    assert r.status_code == 201, r.text
    assert r.json()["estado"] == "CURSANDO"

    r = await cliente.get(f"/seminarios/{seminario['id']}/estudiantes", headers=coord)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["estado"] == "CURSANDO"
    assert r.json()[0]["nota_final"] is None

    r = await cliente.patch(
        f"/seminarios/{seminario['id']}/notas",
        json={"notas": [{"legajo_id": legajo_id, "nota": 8.5}]},
        headers=cabeceras["DOCENTE"],
    )
    assert r.status_code == 200, r.text
    assert r.json()[0]["estado"] == "APROBADO"
    assert r.json()[0]["nota_final"] == 8.5

    r = await cliente.get(f"/seminarios/progreso?legajo_id={legajo_id}", headers=coord)
    assert r.status_code == 200
    assert r.json() == {"obligatorios_total": 1, "aprobados": 1, "adeudados": 0}


async def test_nota_menor_a_4_desaprobe_el_seminario(cliente, cabeceras, oferta, inscribir):
    seminario = await _crear_seminario(cliente, cabeceras, oferta["carreras"][0])
    _token, legajo_id = await inscribir()
    await cliente.post(
        f"/seminarios/{seminario['id']}/estudiantes", json={"legajo_id": legajo_id},
        headers=cabeceras["COORDINADOR"],
    )

    r = await cliente.patch(
        f"/seminarios/{seminario['id']}/notas",
        json={"notas": [{"legajo_id": legajo_id, "nota": 3.9}]},
        headers=cabeceras["DOCENTE"],
    )
    assert r.status_code == 200, r.text
    assert r.json()[0]["estado"] == "DESAPROBADO"

    r = await cliente.get(
        f"/seminarios/progreso?legajo_id={legajo_id}", headers=cabeceras["COORDINADOR"]
    )
    assert r.json() == {"obligatorios_total": 1, "aprobados": 0, "adeudados": 1}


async def test_solo_conduccion_puede_crear_seminarios(cliente, cabeceras, oferta):
    datos = {
        "carrera_id": oferta["carreras"][0], "nombre": "Optativa", "codigo": "OPT-01",
        "horas_catedra": 30,
    }
    assert (
        await cliente.post("/seminarios/", json=datos, headers=cabeceras["DOCENTE"])
    ).status_code == 403
    assert (
        await cliente.post("/seminarios/", json=datos, headers=cabeceras["CPR"])
    ).status_code == 403
    assert (
        await cliente.post("/seminarios/", json={**datos, "codigo": "OPT-02"},
                           headers=cabeceras["DIRECCION"])
    ).status_code == 201


async def test_docente_solo_gestiona_su_propio_seminario(cliente, cabeceras, oferta, inscribir):
    propio = await _crear_seminario(cliente, cabeceras, oferta["carreras"][0])
    ajeno = await _crear_seminario(
        cliente, cabeceras, oferta["carreras"][0],
        codigo="MET-02", docente_email="otro_docente@fenix.test",
    )
    _token, legajo_id = await inscribir()

    assert (
        await cliente.get(f"/seminarios/{propio['id']}/estudiantes", headers=cabeceras["DOCENTE"])
    ).status_code == 200
    assert (
        await cliente.get(f"/seminarios/{ajeno['id']}/estudiantes", headers=cabeceras["DOCENTE"])
    ).status_code == 403

    r = await cliente.post(
        f"/seminarios/{ajeno['id']}/estudiantes", json={"legajo_id": legajo_id},
        headers=cabeceras["COORDINADOR"],
    )
    assert r.status_code == 201
    # El docente ajeno tampoco puede cargar notas en ese seminario
    r = await cliente.patch(
        f"/seminarios/{ajeno['id']}/notas",
        json={"notas": [{"legajo_id": legajo_id, "nota": 7}]},
        headers=cabeceras["DOCENTE"],
    )
    assert r.status_code == 403


async def test_docente_solo_ve_sus_seminarios(cliente, cabeceras, oferta):
    """El listado del portal docente trae solo los seminarios donde está asignado."""
    propio = await _crear_seminario(cliente, cabeceras, oferta["carreras"][0])
    ajeno = await _crear_seminario(
        cliente, cabeceras, oferta["carreras"][1],
        codigo="GER-01", nombre="Gerencia de proyectos", docente_email="otro_docente@fenix.test",
    )

    r = await cliente.get("/seminarios/", headers=cabeceras["DOCENTE"])
    assert r.status_code == 200
    codigos = [s["codigo"] for s in r.json()]
    assert propio["codigo"] in codigos
    assert ajeno["codigo"] not in codigos

    # El parámetro no le permite mirar los de otro docente
    r = await cliente.get(
        "/seminarios/?docente_email=otro_docente@fenix.test", headers=cabeceras["DOCENTE"]
    )
    assert [s["codigo"] for s in r.json()] == [propio["codigo"]]

    # Conducción sí puede filtrar por el docente que quiera
    r = await cliente.get(
        "/seminarios/?docente_email=otro_docente@fenix.test", headers=cabeceras["COORDINADOR"]
    )
    assert [s["codigo"] for s in r.json()] == [ajeno["codigo"]]


async def test_errores_de_seminarios(cliente, cabeceras, oferta, inscribir):
    coord = cabeceras["COORDINADOR"]

    # Carrera inexistente
    r = await cliente.post(
        "/seminarios/",
        json={"carrera_id": "00000000-0000-0000-0000-000000000000", "nombre": "X",
              "codigo": "X-01", "horas_catedra": 10},
        headers=coord,
    )
    assert r.status_code == 404

    seminario = await _crear_seminario(cliente, cabeceras, oferta["carreras"][0])

    # Código duplicado
    r = await cliente.post(
        "/seminarios/",
        json={"carrera_id": oferta["carreras"][0], "nombre": "Otra", "codigo": "MET-01",
              "horas_catedra": 10},
        headers=coord,
    )
    assert r.status_code == 409

    # Seminario inexistente
    assert (
        await cliente.get("/seminarios/00000000-0000-0000-0000-000000000000", headers=coord)
    ).status_code == 404

    # Legajo inexistente
    r = await cliente.post(
        f"/seminarios/{seminario['id']}/estudiantes",
        json={"legajo_id": "00000000-0000-0000-0000-000000000000"}, headers=coord,
    )
    assert r.status_code == 404

    # Doble inscripción del mismo legajo
    _token, legajo_id = await inscribir()
    url = f"/seminarios/{seminario['id']}/estudiantes"
    assert (await cliente.post(url, json={"legajo_id": legajo_id}, headers=coord)).status_code == 201
    assert (await cliente.post(url, json={"legajo_id": legajo_id}, headers=coord)).status_code == 409

    # Nota para un legajo que no está inscripto
    r = await cliente.patch(
        f"/seminarios/{seminario['id']}/notas",
        json={"notas": [{"legajo_id": "00000000-0000-0000-0000-000000000000", "nota": 8}]},
        headers=coord,
    )
    assert r.status_code == 404

    # Notas fuera de rango (schema) y con dos decimales (dominio)
    _token2, legajo2 = await inscribir(dni="35222112")
    await cliente.post(url, json={"legajo_id": legajo2}, headers=coord)
    for nota in (11, 4.55):
        r = await cliente.patch(
            f"/seminarios/{seminario['id']}/notas",
            json={"notas": [{"legajo_id": legajo2, "nota": nota}]},
            headers=coord,
        )
        assert r.status_code == 422, (nota, r.text)

    # Progreso de un legajo inexistente
    r = await cliente.get(
        "/seminarios/progreso?legajo_id=00000000-0000-0000-0000-000000000000", headers=coord
    )
    assert r.status_code == 404
