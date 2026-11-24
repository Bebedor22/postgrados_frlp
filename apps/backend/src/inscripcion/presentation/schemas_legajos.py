"""Esquemas Pydantic de la bandeja y el workflow del coordinador."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.inscripcion.presentation.schemas_inscripcion import TramiteResponse


class LegajoFila(BaseModel):
    """Una fila del listado de inscriptos."""

    id: str
    numero_legajo: str
    apellido: str
    nombre: str
    tipo_documento: str
    documento: str
    email: str
    carrera_id: Optional[str]
    carrera: Optional[str]
    estado: str
    solicita_beca: bool
    tipo_beca: Optional[str]
    fecha_inscripcion: Optional[datetime]


class ListadoLegajosResponse(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    legajos: list[LegajoFila]


class LegajoDetalleResponse(TramiteResponse):
    reserva_vence_el: Optional[date] = Field(None, description="Solo en COMPLETADO (BR-005)")


class ComentarioRequest(BaseModel):
    comentario: str = Field(min_length=10, max_length=1000, examples=["Falta adjuntar la copia del título de grado"])


class MotivoRequest(BaseModel):
    motivo: str = Field(min_length=10, max_length=1000, examples=["La documentación presentada no es válida"])


class CambioEstadoResponse(BaseModel):
    legajo_id: str
    numero_legajo: str
    estado: str


class ReservasVencidasResponse(BaseModel):
    cantidad: int
    legajos: list[CambioEstadoResponse]