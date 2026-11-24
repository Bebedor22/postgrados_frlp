"""Formulario de inscripción por pasos: completitud, porcentaje y validaciones."""
from datetime import date

import pytest

from src.inscripcion.domain.formulario import DatosInvalidos, FormularioInscripcion

HOY = date(2026, 11, 10)
MOTIVACION = "Quiero profundizar mi formación y aplicarla en mi trabajo actual."  # 66 caracteres


def formulario_completo(**cambios) -> FormularioInscripcion:
    datos = dict(
        nombre="Ana", apellido="Rodríguez", tipo_documento="DNI", numero_documento="35222111",
        nacionalidad="Argentina", fecha_nacimiento=date(1993, 5, 20),
        email="ana@mail.com", telefono_movil="221 555-0000", calle="Calle 60", numero="1234",
        codigo_postal="1900", ciudad="La Plata", provincia="Buenos Aires", pais="Argentina",
        titulo_grado="Ingeniería en Sistemas", institucion_grado="UTN FRLP", anio_graduacion=2018,
        como_conocio="EGRESADOS_UTN", motivacion=MOTIVACION,
    )
    datos.update(cambios)
    return FormularioInscripcion(**datos)


def test_formulario_vacio_marca_todo_lo_que_falta():
    formulario = FormularioInscripcion()
    faltantes = formulario.faltantes_por_paso()
    assert "nombre" in faltantes[1] and "fecha_nacimiento" in faltantes[1]
    assert "telefono_movil" in faltantes[2]
    assert "motivacion" in faltantes[3]
    assert faltantes[4] == []  # Sin beca, el paso 4 no pide nada
    assert formulario.porcentaje_completo() == 0
    assert not formulario.esta_completo()


def test_formulario_completo():
    formulario = formulario_completo()
    assert formulario.esta_completo()
    assert formulario.porcentaje_completo() == 100


def test_porcentaje_parcial():
    formulario = formulario_completo(telefono_movil=None, calle=None)
    assert 0 < formulario.porcentaje_completo() < 100
    assert formulario.faltantes_por_paso()[2] == ["telefono_movil", "calle"]


def test_motivacion_de_menos_de_50_caracteres_cuenta_como_faltante():
    """REQ-CORE-001: motivación de al menos 50 caracteres."""
    formulario = formulario_completo(motivacion="Me interesa la carrera.")
    assert formulario.faltantes_por_paso()[3] == ["motivacion"]
    assert not formulario.esta_completo()
    # Pero se puede guardar igual ("cargar y guardar")
    formulario.actualizar({"motivacion": "Corta"}, HOY)


def test_beca_pide_el_tipo():
    formulario = formulario_completo(solicita_beca=True)
    assert formulario.faltantes_por_paso()[4] == ["tipo_beca"]
    formulario.actualizar({"tipo_beca": "30"}, HOY)
    assert formulario.esta_completo()


def test_sin_beca_se_borra_el_tipo():
    formulario = formulario_completo(solicita_beca=True, tipo_beca="100")
    formulario.actualizar({"solicita_beca": False}, HOY)
    assert formulario.tipo_beca is None


def test_como_conocio_otros_pide_detalle():
    formulario = formulario_completo(como_conocio="OTROS")
    assert "como_conocio_detalle" in formulario.faltantes_por_paso()[3]


def test_textos_vacios_se_guardan_como_sin_completar():
    formulario = formulario_completo()
    formulario.actualizar({"calle": "   "}, HOY)
    assert formulario.calle is None


@pytest.mark.parametrize("cambios, mensaje", [
    ({"fecha_nacimiento": date(2030, 1, 1)}, "anterior a hoy"),
    ({"anio_graduacion": 1900}, "entre 1950"),
    ({"anio_graduacion": 2099}, "entre 1950"),
    ({"como_conocio": "TELEVISION"}, "como_conocio"),
    ({"solicita_beca": True, "tipo_beca": "50"}, "30% o del 100%"),
    ({"motivacion": "x" * 501}, "hasta 500"),
    ({"campo_inventado": "x"}, "Campo desconocido"),
])
def test_datos_invalidos(cambios, mensaje):
    with pytest.raises(DatosInvalidos, match=mensaje):
        FormularioInscripcion().actualizar(cambios, HOY)