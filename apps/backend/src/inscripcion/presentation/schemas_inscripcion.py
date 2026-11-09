"""Esquemas Pydantic de la inscripción por pasos (formulario del aspirante)."""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ComoConocio = Literal["SITIO_WEB", "OTROS_SITIOS_WEB", "EGRESADOS_UTN", "COLEGAS", "OTROS"]


class InicioInscripcion(BaseModel):
    """Datos mínimos para iniciar: con esto se crea el legajo en BORRADOR."""

    cohorte_id: str
    carrera_id: str
    tipo_documento: Literal["DNI", "PASAPORTE"] = "DNI"
    numero_documento: str = Field(min_length=6, max_length=12, examples=["30111222"])
    nombre: str = Field(min_length=1, max_length=100, examples=["Ana Laura"])
    apellido: str = Field(min_length=1, max_length=100, examples=["Rodríguez"])
    email: str = Field(min_length=5, max_length=255, examples=["ana.rodriguez@gmail.com"])


class DatosFormulario(BaseModel):
    """Guardado parcial: se mandan solo los campos que se quieren guardar."""

    # Un campo desconocido (o uno que no se puede cambiar, como el documento) da 422
    model_config = ConfigDict(extra="forbid")

    # Paso 1 — Datos personales
    nombre: Optional[str] = Field(None, max_length=100)
    apellido: Optional[str] = Field(None, max_length=100)
    nacionalidad: Optional[str] = Field(None, max_length=60, examples=["Argentina"])
    fecha_nacimiento: Optional[date] = Field(None, examples=["1995-06-15"])
    genero: Optional[str] = Field(None, max_length=30)
    # Paso 2 — Contacto y domicilio
    email: Optional[str] = Field(None, max_length=255)
    email_alternativo: Optional[str] = Field(None, max_length=255)
    telefono_movil: Optional[str] = Field(None, max_length=30, examples=["+54 9 221 555-1234"])
    telefono_fijo: Optional[str] = Field(None, max_length=30)
    calle: Optional[str] = Field(None, max_length=120, examples=["Calle 60"])
    numero: Optional[str] = Field(None, max_length=10, examples=["1234"])
    piso_depto: Optional[str] = Field(None, max_length=20)
    codigo_postal: Optional[str] = Field(None, max_length=10, examples=["1900"])
    ciudad: Optional[str] = Field(None, max_length=80, examples=["La Plata"])
    provincia: Optional[str] = Field(None, max_length=80, examples=["Buenos Aires"])
    pais: Optional[str] = Field(None, max_length=60, examples=["Argentina"])
    # Paso 3 — Formación y motivación
    titulo_grado: Optional[str] = Field(None, max_length=150, examples=["Ingeniería en Sistemas de Información"])
    institucion_grado: Optional[str] = Field(None, max_length=150, examples=["UTN FRLP"])
    anio_graduacion: Optional[int] = Field(None, examples=[2019])
    titulo_posgrado: Optional[str] = Field(None, max_length=150)
    como_conocio: Optional[ComoConocio] = None
    como_conocio_detalle: Optional[str] = Field(None, max_length=150)
    motivacion: Optional[str] = Field(None, max_length=500)
    trabaja_en_area: Optional[bool] = None
    # Paso 4 — Beca
    solicita_beca: Optional[bool] = None
    tipo_beca: Optional[Literal["30", "100"]] = None


class ProgresoResponse(BaseModel):
    porcentaje: int = Field(description="Indicador de estado de carga del legajo (0 a 100)")
    completo: bool
    faltantes_por_paso: dict[int, list[str]]


class CambioDeEstadoResponse(BaseModel):
    estado_anterior: Optional[str]
    estado_nuevo: str
    comentario: Optional[str]
    fecha: datetime


class TramiteResponse(BaseModel):
    legajo_id: str
    numero_legajo: str
    estado: str
    puede_editar: bool
    cohorte_id: str
    carrera_id: Optional[str]
    datos: dict
    progreso: ProgresoResponse
    historial: list[CambioDeEstadoResponse]


class InscripcionIniciadaResponse(BaseModel):
    legajo_id: str
    estado: str
    token: str = Field(description="Guardalo: es la única forma de retomar la inscripción")
    link_seguimiento: str