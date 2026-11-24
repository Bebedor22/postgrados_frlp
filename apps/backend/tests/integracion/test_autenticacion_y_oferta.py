"""Login, permisos por rol, carreras y cohortes (BR-009)."""


async def test_login_correcto_devuelve_token_y_usuario(cliente):
    r = await cliente.post("/auth/login", json={"email": "admin@fenix.test", "password": "Admin1234!"})
    assert r.status_code == 200
    assert r.json()["usuario"]["rol"] == "COORDINADOR"
    yo = await cliente.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert yo.json()["email"] == "admin@fenix.test"


async def test_login_incorrecto_da_el_mismo_error_exista_o_no_el_email(cliente):
    mal_password = await cliente.post("/auth/login", json={"email": "admin@fenix.test", "password": "otra"})
    no_existe = await cliente.post("/auth/login", json={"email": "nadie@fenix.test", "password": "otra"})
    assert mal_password.status_code == no_existe.status_code == 401
    assert mal_password.json() == no_existe.json()


async def test_sin_token_o_con_token_falso_da_401(cliente):
    assert (await cliente.get("/legajos/")).status_code == 401
    assert (await cliente.get("/legajos/", headers={"Authorization": "Bearer inventado"})).status_code == 401


async def test_rol_sin_permiso_da_403(cliente, cabeceras):
    r = await cliente.get("/legajos/", headers=cabeceras["DOCENTE"])
    assert r.status_code == 403


async def test_carreras_y_cohortes(cliente, cabeceras, oferta):
    carreras = (await cliente.get("/carreras/")).json()
    assert len(carreras) == 3
    # Nombre repetido
    r = await cliente.post("/carreras/", json={"nombre": "Maestría en Sistemas", "tipo": "Maestria", "duracion_anios": 2},
                           headers=cabeceras["COORDINADOR"])
    assert r.status_code == 409
    abiertas = (await cliente.get("/cohortes/", params={"solo_abiertas": True})).json()
    assert [c["nombre"] for c in abiertas] == ["Cohorte 2027"]


async def test_solo_la_coordinacion_abre_o_cierra_la_inscripcion(cliente, cabeceras, oferta):
    """BR-009."""
    ruta = f"/cohortes/{oferta['cohorte']}/inscripcion"
    assert (await cliente.patch(ruta, json={"abierta": False}, headers=cabeceras["DIRECCION"])).status_code == 403
    assert (await cliente.patch(ruta, json={"abierta": False})).status_code == 401
    r = await cliente.patch(ruta, json={"abierta": False}, headers=cabeceras["COORDINADOR"])
    assert r.status_code == 200 and r.json()["inscripcion_abierta"] is False
    # Cerrar una cohorte ya cerrada
    assert (await cliente.patch(ruta, json={"abierta": False}, headers=cabeceras["COORDINADOR"])).status_code == 409


async def test_cohorte_inexistente(cliente, cabeceras):
    r = await cliente.patch("/cohortes/no-existe/inscripcion", json={"abierta": True}, headers=cabeceras["COORDINADOR"])
    assert r.status_code == 404