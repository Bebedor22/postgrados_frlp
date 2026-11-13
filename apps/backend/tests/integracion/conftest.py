"""Fixtures de los tests de integración: base de datos real y la API completa.

- Al empezar, se crea la base `postgrado_test` (si no existe) y se aplican todas las
  migraciones desde cero: así también se prueba que las migraciones funcionan.
- Antes de cada test se vacían las tablas (menos la de usuarios).
- `cliente` llama a la API sin levantar un servidor (httpx + ASGITransport).
"""
import asyncio
from urllib.parse import urlsplit

import asyncpg
import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from ayudas import CONTRASENAS, DOCUMENTOS_OBLIGATORIOS, EMAILS, FORMULARIO_COMPLETO, subir
from main import app
from scripts.crear_usuarios_iniciales import USUARIOS_DE_PRUEBA
from src.autenticacion.application.registrar_usuario import registrar_usuario
from src.autenticacion.infrastructure.bcrypt_hasher import BcryptHasher
from src.autenticacion.infrastructure.pg_repository import PostgresUsuarioRepository
from src.inscripcion.infrastructure import email_notifier
from src.shared.config import get_settings
from src.shared.database.connection import AsyncSessionLocal, engine

async def _crear_base_si_no_existe(url: str) -> None:
    partes = urlsplit(url.replace("+asyncpg", ""))
    nombre = partes.path.lstrip("/")
    conexion = await asyncpg.connect(
        user=partes.username, password=partes.password, host=partes.hostname,
        port=partes.port or 5432, database="postgres",
    )
    try:
        if not await conexion.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", nombre):
            await conexion.execute(f'CREATE DATABASE "{nombre}"')
    finally:
        await conexion.close()


@pytest.fixture(scope="session", autouse=True)
def base_de_datos():
    """Base de test migrada desde cero (prueba también el downgrade de todas las migraciones)."""
    asyncio.run(_crear_base_si_no_existe(get_settings().database_url))
    alembic = Config("alembic.ini")
    command.downgrade(alembic, "base")
    command.upgrade(alembic, "head")


@pytest.fixture(scope="session", autouse=True)
async def usuarios(base_de_datos):
    """Los 4 usuarios de prueba (una sola vez: bcrypt es lento a propósito)."""
    async with AsyncSessionLocal() as session:
        repo = PostgresUsuarioRepository(session)
        for email, nombre, rol, contrasena in USUARIOS_DE_PRUEBA:
            await registrar_usuario(email, nombre, rol, contrasena, repo, BcryptHasher())
        await session.commit()
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
async def tablas_vacias(usuarios):
    async with engine.begin() as conexion:
        await conexion.execute(text("TRUNCATE legajos, cohortes, carreras RESTART IDENTITY CASCADE"))


@pytest.fixture
async def cliente():
    transporte = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transporte, base_url="http://test/api/v1", follow_redirects=True) as c:
        yield c


@pytest.fixture(scope="session")
async def cabeceras(usuarios):
    """Encabezado Authorization de cada rol: {"COORDINADOR": {...}, "DIRECCION": {...}, ...}."""
    transporte = httpx.ASGITransport(app=app)
    resultado = {}
    async with httpx.AsyncClient(transport=transporte, base_url="http://test/api/v1") as c:
        for rol, email in EMAILS.items():
            r = await c.post("/auth/login", json={"email": email, "password": CONTRASENAS[rol]})
            resultado[rol] = {"Authorization": f"Bearer {r.json()['access_token']}"}
    return resultado


@pytest.fixture
def emails(monkeypatch):
    """Junta los emails que mandaría el sistema, en lugar de enviarlos."""
    enviados = []
    monkeypatch.setattr(email_notifier, "enviar_email", enviados.append)
    return enviados


@pytest.fixture
async def oferta(cliente, cabeceras):
    """3 carreras y la Cohorte 2027 con la inscripción abierta."""
    coord = cabeceras["COORDINADOR"]
    carreras = []
    for nombre, tipo, anios in [("Maestría en Sistemas", "Maestria", 2), ("Especialización Gerencial", "Especializacion", 1),
                                ("Doctorado en Ingeniería", "Doctorado", 4)]:
        r = await cliente.post("/carreras/", json={"nombre": nombre, "tipo": tipo, "duracion_anios": anios}, headers=coord)
        carreras.append(r.json()["id"])
    r = await cliente.post("/cohortes/", json={"anio": 2027, "nombre": "Cohorte 2027"}, headers=coord)
    cohorte = r.json()["id"]
    await cliente.patch(f"/cohortes/{cohorte}/inscripcion", json={"abierta": True}, headers=coord)
    return {"cohorte": cohorte, "carreras": carreras}


@pytest.fixture
def inscribir(cliente, oferta):
    """Crea una inscripción y la lleva hasta donde se pida. Devuelve (token, legajo_id)."""

    async def _inscribir(dni="35222111", carrera=0, completar=True, documentos=True, enviar=True, **datos):
        r = await cliente.post("/inscripciones/", json={
            "cohorte_id": oferta["cohorte"], "carrera_id": oferta["carreras"][carrera], "tipo_documento": "DNI",
            "numero_documento": dni, "nombre": "Ana", "apellido": "Rodríguez", "email": "ana@mail.com",
        })
        assert r.status_code == 201, r.text
        token, legajo_id = r.json()["token"], r.json()["legajo_id"]
        if completar:
            assert (await cliente.patch(f"/inscripciones/{token}", json={**FORMULARIO_COMPLETO, **datos})).status_code == 200
        if documentos:
            for tipo in DOCUMENTOS_OBLIGATORIOS:
                await subir(cliente, token, tipo)
        if enviar:
            r = await cliente.post(f"/inscripciones/{token}/confirmar")
            assert r.status_code == 200, r.text
        return token, legajo_id

    return _inscribir