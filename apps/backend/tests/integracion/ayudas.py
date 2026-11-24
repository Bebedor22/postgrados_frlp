"""Datos y funciones que comparten los tests de integración."""
from scripts.crear_usuarios_iniciales import USUARIOS_DE_PRUEBA
from scripts.seed import pdf_de_ejemplo

CONTRASENAS = {rol.value: contrasena for _email, _nombre, rol, contrasena in USUARIOS_DE_PRUEBA}
EMAILS = {rol.value: email for email, _nombre, rol, _contrasena in USUARIOS_DE_PRUEBA}
FORMULARIO_COMPLETO = {
    "nacionalidad": "Argentina", "fecha_nacimiento": "1993-05-20", "telefono_movil": "221 555-0000",
    "calle": "Calle 60", "numero": "1234", "codigo_postal": "1900", "ciudad": "La Plata",
    "provincia": "Buenos Aires", "pais": "Argentina", "titulo_grado": "Ingeniería en Sistemas",
    "institucion_grado": "UTN FRLP", "anio_graduacion": 2018, "como_conocio": "EGRESADOS_UTN",
    "motivacion": "Quiero profundizar mi formación y aplicarla en mi trabajo actual.",
}
DOCUMENTOS_OBLIGATORIOS = ["FORM_INSCRIPCION", "DNI", "TITULO_GRADO", "PARTIDA", "CUIT_CUIL"]
PDF = pdf_de_ejemplo("Documento de prueba")


async def subir(cliente, token, tipo, contenido=PDF, nombre="documento.pdf", tipo_mime="application/pdf"):
    return await cliente.post(
        f"/inscripciones/{token}/documentos", data={"tipo": tipo}, files={"archivo": (nombre, contenido, tipo_mime)}
    )