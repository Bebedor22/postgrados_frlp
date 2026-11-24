"""Esquemas Pydantic de carreras y cohortes."""
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

TipoCarreraLiteral = Literal["Especializacion", "Maestria", "Doctorado"]


class CarreraCrear(BaseModel):
    nombre: str = Field(min_length=3, max_length=150, examples=["Maestría en Ingeniería en Sistemas de Información"])
    tipo: TipoCarreraLiteral
    duracion_anios: int = Field(ge=1, le=6, examples=[2])


class CarreraResponse(BaseModel):
    id: str
    nombre: str
    tipo: str
    duracion_anios: int
    activa: bool


class CohorteCrear(BaseModel):
    anio: int = Field(ge=2000, le=2100, examples=[2027])
    nombre: str = Field(min_length=3, max_length=50, examples=["Cohorte 2027"])
    fecha_inicio: Optional[date] = None


class CohorteResponse(BaseModel):
    id: str
    anio: int
    nombre: str
    inscripcion_abierta: bool
    fecha_inicio: Optional[date]


class CambioInscripcion(BaseModel):
    abierta: bool = Field(description="true abre la inscripción, false la cierra")