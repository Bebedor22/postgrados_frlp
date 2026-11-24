"""Inscripción por pasos del aspirante (RF-CORE-001) y reglas BR-001 y BR-009."""
from ayudas import FORMULARIO_COMPLETO


async def test_flujo_de_inscripcion_completo(cliente, inscribir, emails):
    token, _ = await inscribir()
    tramite = (await cliente.get(f"/inscripciones/{token}")).json()
    assert tramite["estado"] == "PENDIENTE"
    assert tramite["progreso"]["porcentaje"] == 100
    assert tramite["puede_editar"] is False
    assert [h["estado_nuevo"] for h in tramite["historial"]] == ["BORRADOR", "PENDIENTE"]
    asuntos = [e.asunto for e in emails]
    assert "Tu inscripción al posgrado: link de seguimiento" in asuntos
    assert "Recibimos tu inscripción" in asuntos
    assert any(f"/tramite/{token}" in e.cuerpo for e in emails)


async def test_guardar_y_seguir_despues(cliente, inscribir):
    token, _ = await inscribir(completar=False, documentos=False, enviar=False)
    r = await cliente.patch(f"/inscripciones/{token}", json={"nacionalidad": "Argentina", "telefono_movil": "221 555"})
    assert r.status_code == 200
    progreso = r.json()["progreso"]
    assert 0 < progreso["porcentaje"] < 100
    assert "nacionalidad" not in progreso["faltantes_por_paso"]["1"]
    # Otro día vuelve con el mismo link y sigue donde estaba
    tramite = (await cliente.get(f"/inscripciones/{token}")).json()
    assert tramite["datos"]["nacionalidad"] == "Argentina"


async def test_no_se_envia_incompleto(cliente, inscribir):
    token, _ = await inscribir(completar=False, documentos=False, enviar=False)
    r = await cliente.post(f"/inscripciones/{token}/confirmar")
    assert r.status_code == 409 and "Faltan completar" in r.json()["detail"]


async def test_motivacion_corta_no_deja_enviar(cliente, inscribir):
    token, _ = await inscribir(enviar=False, motivacion="Me interesa.")
    r = await cliente.post(f"/inscripciones/{token}/confirmar")
    assert r.status_code == 409 and "motivacion" in r.json()["detail"]


async def test_no_se_modifica_despues_de_enviar(cliente, inscribir):
    token, _ = await inscribir()
    r = await cliente.patch(f"/inscripciones/{token}", json={"ciudad": "Berisso"})
    assert r.status_code == 409
    assert (await cliente.post(f"/inscripciones/{token}/confirmar")).status_code == 409


async def test_el_documento_no_se_cambia(cliente, inscribir):
    token, _ = await inscribir(completar=False, documentos=False, enviar=False)
    r = await cliente.patch(f"/inscripciones/{token}", json={"numero_documento": "11111111"})
    assert r.status_code == 422  # El esquema no lo acepta (extra="forbid")


async def test_datos_invalidos(cliente, inscribir, oferta):
    token, _ = await inscribir(completar=False, documentos=False, enviar=False)
    assert (await cliente.patch(f"/inscripciones/{token}", json={"anio_graduacion": 1800})).status_code == 422
    assert (await cliente.patch(f"/inscripciones/{token}", json={"email": "sin-arroba"})).status_code == 422
    r = await cliente.post("/inscripciones/", json={
        "cohorte_id": oferta["cohorte"], "carrera_id": oferta["carreras"][0], "tipo_documento": "DNI",
        "numero_documento": "12.345.678", "nombre": "A", "apellido": "B", "email": "a@b.com",
    })
    assert r.status_code == 422


async def test_token_inexistente(cliente):
    assert (await cliente.get("/inscripciones/no-existe")).status_code == 404
    assert (await cliente.patch("/inscripciones/no-existe", json={"ciudad": "X"})).status_code == 404
    assert (await cliente.post("/inscripciones/no-existe/confirmar")).status_code == 404


async def test_maximo_dos_carreras_por_cohorte(cliente, inscribir, oferta):
    """BR-001."""
    await inscribir(carrera=0, completar=False, documentos=False, enviar=False)
    await inscribir(carrera=1, completar=False, documentos=False, enviar=False)
    r = await cliente.post("/inscripciones/", json={
        "cohorte_id": oferta["cohorte"], "carrera_id": oferta["carreras"][2], "tipo_documento": "DNI",
        "numero_documento": "35222111", "nombre": "Ana", "apellido": "Rodríguez", "email": "ana@mail.com",
    })
    assert r.status_code == 409 and "BR-001" in r.json()["detail"]


async def test_no_se_inscribe_dos_veces_a_la_misma_carrera(cliente, inscribir, oferta):
    await inscribir(completar=False, documentos=False, enviar=False)
    r = await cliente.post("/inscripciones/", json={
        "cohorte_id": oferta["cohorte"], "carrera_id": oferta["carreras"][0], "tipo_documento": "DNI",
        "numero_documento": "35222111", "nombre": "Ana", "apellido": "Rodríguez", "email": "ana@mail.com",
    })
    assert r.status_code == 409 and "Ya existe" in r.json()["detail"]


async def test_cohorte_cerrada_no_acepta_inscripciones(cliente, cabeceras, oferta):
    """BR-009."""
    await cliente.patch(f"/cohortes/{oferta['cohorte']}/inscripcion", json={"abierta": False}, headers=cabeceras["COORDINADOR"])
    r = await cliente.post("/inscripciones/", json={
        "cohorte_id": oferta["cohorte"], "carrera_id": oferta["carreras"][0], "tipo_documento": "PASAPORTE",
        "numero_documento": "AAB123456", "nombre": "Ana", "apellido": "R", "email": "a@b.com",
    })
    assert r.status_code == 409


async def test_beca(cliente, inscribir):
    token, _ = await inscribir(enviar=False, solicita_beca=True)
    tramite = (await cliente.get(f"/inscripciones/{token}")).json()
    assert tramite["progreso"]["faltantes_por_paso"]["4"] == ["tipo_beca"]
    assert "FORM_BECA" in [d["tipo"] for d in tramite["documentos"] if d["obligatorio"]]
    datos = {**FORMULARIO_COMPLETO, "solicita_beca": True, "tipo_beca": "100"}
    assert (await cliente.patch(f"/inscripciones/{token}", json=datos)).json()["progreso"]["completo"]