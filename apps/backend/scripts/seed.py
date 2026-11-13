"""Carga datos de demo para mostrar el sistema funcionando (solo desarrollo).

Uso (con Docker levantado, desde la raíz del repo):
    docker compose exec backend python -m scripts.seed

Con `--automatico` (así lo corre docker-compose al arrancar el backend) solo carga
los datos si la base está vacía y DATOS_DEMO no es "no". Así nunca pisa lo que se
hizo durante una demo (por ejemplo, volver a abrir una inscripción cerrada).

Crea:
- los 4 usuarios de prueba (coordinación, docente, CPR y Dirección);
- 3 carreras (una de cada tipo);
- 2 cohortes: 2026 (inscripción cerrada) y 2027 (inscripción abierta);
- 16 aspirantes ficticios en la Cohorte 2027, repartidos en todos los estados del workflow,
  con sus documentos PDF de ejemplo (los que ya enviaron la inscripción).

Usa los mismos casos de uso que la API, así los datos respetan todas las reglas
del dominio. Se puede correr más de una vez: lo que ya existe no se duplica.
"""
import asyncio
import os
import sys
from datetime import date

from src.autenticacion.application.registrar_usuario import UsuarioYaExiste, registrar_usuario
from src.gestion_documental.application.gestionar_documentos import subir_documento
from src.gestion_documental.domain.entities import documentos_faltantes
from src.gestion_documental.infrastructure.file_storage import AlmacenamientoLocal
from src.gestion_documental.infrastructure.pg_repository import PostgresDocumentoRepository
from src.autenticacion.infrastructure.bcrypt_hasher import BcryptHasher
from src.autenticacion.infrastructure.pg_repository import PostgresUsuarioRepository
from src.inscripcion.application.gestionar_legajos import (
    aprobar_legajo,
    matricular_legajo,
    observar_legajo,
    rechazar_legajo,
    revisar_legajo,
)
from src.inscripcion.application.inscripcion_por_pasos import (
    confirmar_inscripcion,
    consultar_tramite,
    guardar_progreso,
    iniciar_inscripcion,
)
from src.inscripcion.domain.repo import FiltrosLegajos
from src.inscripcion.infrastructure.pg_repository import PostgresLegajoRepository
from src.oferta_academica.application.gestionar_carreras import CarreraYaExiste, crear_carrera
from src.oferta_academica.application.gestionar_cohortes import cambiar_estado_inscripcion, crear_cohorte
from src.oferta_academica.infrastructure.pg_repository import PostgresCarreraRepository, PostgresCohorteRepository
from src.shared.config import get_settings
from src.shared.database.connection import AsyncSessionLocal, engine

from scripts.crear_usuarios_iniciales import USUARIOS_DE_PRUEBA

COORDINADOR = "admin@fenix.test"

CARRERAS = [
    ("Maestría en Ingeniería en Sistemas de Información", "Maestria", 2),
    ("Especialización en Ingeniería Gerencial", "Especializacion", 1),
    ("Doctorado en Ingeniería", "Doctorado", 4),
]

# (apellido, nombre, DNI, índice de carrera, estado final, ¿beca?)
ASPIRANTES = [
    ("Rodríguez", "Ana Laura", "35222111", 0, "PENDIENTE", "30"),
    ("Gómez", "Martín", "32360893", 0, "PENDIENTE", None),
    ("Sosa", "Valentina", "38111222", 1, "PENDIENTE", None),
    ("Herrera", "Tomás", "36455120", 2, "PENDIENTE", "100"),
    ("Acosta", "Federico", "33908741", 1, "PENDIENTE", None),
    ("Molina", "Julieta", "39222876", 0, "EN_REVISION", None),
    ("Castro", "Nicolás", "34777012", 2, "EN_REVISION", "30"),
    ("Ríos", "Camila", "37010455", 1, "OBSERVADO", None),
    ("Ortiz", "Agustina", "40123987", 0, "OBSERVADO", "30"),
    ("Fernández", "Lucía", "31877220", 0, "COMPLETADO", None),
    ("Benítez", "Joaquín", "35987456", 2, "COMPLETADO", "100"),
    ("Medina", "Sofía", "36222333", 1, "ACTIVO", None),
    ("Romero", "Bruno", "34111999", 0, "ACTIVO", None),
    ("Silva", "Carolina", "38765432", 1, "RECHAZADO", None),
    ("Torres", "Matías", "41234567", 0, "BORRADOR_AVANZADO", None),
    ("Vega", "Paula", "42345678", 2, "BORRADOR", None),
]

FORMULARIO_BASE = {
    "nacionalidad": "Argentina",
    "fecha_nacimiento": date(1993, 5, 20),
    "telefono_movil": "+54 9 221 555-0000",
    "calle": "Calle 60",
    "numero": "1234",
    "codigo_postal": "1900",
    "ciudad": "La Plata",
    "provincia": "Buenos Aires",
    "pais": "Argentina",
    "titulo_grado": "Ingeniería en Sistemas de Información",
    "institucion_grado": "UTN Facultad Regional La Plata",
    "anio_graduacion": 2018,
    "como_conocio": "EGRESADOS_UTN",
    "motivacion": "Quiero profundizar mi formación y aplicarla en mi trabajo actual.",
    "trabaja_en_area": True,
}

def pdf_de_ejemplo(texto: str) -> bytes:
    """Un PDF mínimo de una página con un texto (para los documentos de demo)."""
    texto = texto.encode("latin-1", "replace").decode("latin-1").replace("(", "[").replace(")", "]")
    contenido = f"BT /F1 18 Tf 60 760 Td ({texto}) Tj ET".encode("latin-1")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(contenido) + contenido + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    posiciones = []
    for numero, objeto in enumerate(objetos, start=1):
        posiciones.append(len(pdf))
        pdf += b"%d 0 obj\n" % numero + objeto + b"\nendobj\n"
    inicio_xref = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for posicion in posiciones:
        pdf += b"%010d 00000 n \n" % posicion
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objetos) + 1, inicio_xref)
    return bytes(pdf)


async def subir_documentos_de_ejemplo(token: str, apellido: str, session) -> None:
    """Sube un PDF de ejemplo por cada documento obligatorio que falte."""
    repo_legajos = PostgresLegajoRepository(session)
    repo_documentos = PostgresDocumentoRepository(session)
    almacenamiento = AlmacenamientoLocal(get_settings().storage_path)
    tramite = await consultar_tramite(token, repo_legajos, repo_documentos)
    for tipo in documentos_faltantes(tramite.documentos):
        await subir_documento(
            token, tipo.value, f"{tipo.value.lower()}_{apellido.lower()}.pdf",
            pdf_de_ejemplo(f"{tipo.descripcion} - {apellido} (documento de ejemplo)"),
            repo_legajos, repo_documentos, almacenamiento,
        )


OBSERVACIONES = {
    "Ríos": "Falta adjuntar la copia del título de grado legalizada.",
    "Ortiz": "El año de graduación no coincide con el que figura en el título.",
}


async def crear_usuarios() -> None:
    async with AsyncSessionLocal() as session:
        repo = PostgresUsuarioRepository(session)
        for email, nombre, rol, contrasena in USUARIOS_DE_PRUEBA:
            try:
                await registrar_usuario(email, nombre, rol, contrasena, repo, BcryptHasher())
                print(f"  ✔ Usuario {email} ({rol.value})")
            except UsuarioYaExiste:
                print(f"  • Usuario {email} ya existía")
        await session.commit()


async def crear_oferta() -> tuple[list[str], str]:
    """Devuelve los ids de las carreras y el id de la cohorte abierta (2027)."""
    async with AsyncSessionLocal() as session:
        repo_carreras = PostgresCarreraRepository(session)
        repo_cohortes = PostgresCohorteRepository(session)

        ids_carreras = []
        for nombre, tipo, duracion in CARRERAS:
            try:
                carrera = await crear_carrera(nombre, tipo, duracion, repo_carreras)
                print(f"  ✔ Carrera {nombre}")
            except CarreraYaExiste:
                carrera = await repo_carreras.obtener_por_nombre(nombre)
                print(f"  • Carrera {nombre} ya existía")
            ids_carreras.append(carrera.id)

        cohortes = {}
        for anio, nombre in [(2026, "Cohorte 2026"), (2027, "Cohorte 2027")]:
            cohorte = await repo_cohortes.obtener_por_nombre(nombre)
            if cohorte is None:
                cohorte = await crear_cohorte(anio, nombre, repo_cohortes, date(anio, 4, 1))
                print(f"  ✔ {nombre}")
            else:
                print(f"  • {nombre} ya existía")
            cohortes[anio] = cohorte

        # La 2027 es la que recibe inscripciones; la 2026 queda cerrada
        if not cohortes[2027].inscripcion_abierta:
            await cambiar_estado_inscripcion(cohortes[2027].id, True, repo_cohortes)
            print("  ✔ Inscripción de la Cohorte 2027 abierta")
        if cohortes[2026].inscripcion_abierta:
            await cambiar_estado_inscripcion(cohortes[2026].id, False, repo_cohortes)
            print("  ✔ Inscripción de la Cohorte 2026 cerrada")
        await session.commit()
        return ids_carreras, cohortes[2027].id


async def crear_aspirante(datos: tuple, ids_carreras: list[str], cohorte_id: str) -> tuple[str, str]:
    """Inscribe a un aspirante y lo lleva hasta su estado final. Devuelve (apellido, token)."""
    apellido, nombre, dni, i_carrera, estado, beca = datos
    async with AsyncSessionLocal() as session:
        repo = PostgresLegajoRepository(session)
        repo_documentos = PostgresDocumentoRepository(session)
        legajo, token = await iniciar_inscripcion(
            cohorte_id=cohorte_id,
            carrera_id=ids_carreras[i_carrera],
            tipo_documento="DNI",
            numero_documento=dni,
            nombre=nombre,
            apellido=apellido,
            email=f"{nombre.split()[0].lower()}.{apellido.lower()}@mail.com".translate(str.maketrans("áéíóú", "aeiou")),
            repo=repo,
            repo_cohortes=PostgresCohorteRepository(session),
            repo_carreras=PostgresCarreraRepository(session),
        )
        if estado == "BORRADOR":  # solo el paso inicial
            await session.commit()
            return apellido, token

        formulario = dict(FORMULARIO_BASE)
        if beca:
            formulario.update(solicita_beca=True, tipo_beca=beca)
        if estado == "BORRADOR_AVANZADO":  # completó hasta el paso 2
            formulario = {k: v for k, v in formulario.items() if k not in ("titulo_grado", "motivacion", "como_conocio")}
        await guardar_progreso(token, formulario, repo, repo_documentos)
        if estado == "BORRADOR_AVANZADO":
            await session.commit()
            return apellido, token

        await subir_documentos_de_ejemplo(token, apellido, session)
        await confirmar_inscripcion(token, repo, repo_documentos)  # → PENDIENTE
        if estado == "OBSERVADO":
            await observar_legajo(legajo.id, OBSERVACIONES[apellido], repo, COORDINADOR)
        elif estado != "PENDIENTE":
            await revisar_legajo(legajo.id, repo, COORDINADOR)  # → EN_REVISION
            if estado == "RECHAZADO":
                await rechazar_legajo(legajo.id, "La carrera requiere un título de grado afín.", repo, COORDINADOR)
            elif estado in ("COMPLETADO", "ACTIVO"):
                await aprobar_legajo(legajo.id, repo, PostgresCohorteRepository(session), COORDINADOR)
                if estado == "ACTIVO":
                    await matricular_legajo(legajo.id, repo, COORDINADOR)
        await session.commit()
        return apellido, token


async def hay_datos() -> bool:
    async with AsyncSessionLocal() as session:
        return bool(await PostgresCohorteRepository(session).listar())


async def main() -> None:
    if "--automatico" in sys.argv:
        if os.environ.get("DATOS_DEMO", "si").lower() in ("no", "false", "0"):
            print("DATOS_DEMO=no: no se cargan datos de demo")
            await engine.dispose()
            return
        if await hay_datos():
            print("La base ya tiene datos: no se cargan los de demo")
            await engine.dispose()
            return

    print("\n▶ Usuarios")
    await crear_usuarios()
    print("\n▶ Carreras y cohortes")
    ids_carreras, cohorte_id = await crear_oferta()

    print("\n▶ Aspirantes")
    async with AsyncSessionLocal() as session:
        _, cantidad = await PostgresLegajoRepository(session).buscar(FiltrosLegajos(cohorte_id=cohorte_id, por_pagina=1))
    if cantidad > 0:
        print(f"  • La Cohorte 2027 ya tiene {cantidad} legajos: no se cargan aspirantes de demo")
        await engine.dispose()
        return

    links = {}
    for datos in ASPIRANTES:
        apellido, token = await crear_aspirante(datos, ids_carreras, cohorte_id)
        links[apellido] = token
        print(f"  ✔ {apellido}, {datos[1]} → {datos[4].replace('_AVANZADO', '')}")
    await engine.dispose()

    url = get_settings().frontend_url
    print("\n▶ Listo. Para la demo:")
    print("  Coordinación: admin@fenix.test / Admin1234!   (http://localhost:8081/login)")
    print("  Dirección:    direccion@fenix.test / Direccion1234!")
    print(f"  Trámite observado (Ríos):        {url}/tramite/{links['Ríos']}")
    print(f"  Trámite a medio completar (Torres): {url}/tramite/{links['Torres']}\n")


if __name__ == "__main__":
    asyncio.run(main())