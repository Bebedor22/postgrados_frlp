"""Respuestas del avance académico que consulta el alumno con el token de su trámite."""
from typing import Optional

from pydantic import BaseModel


class ProgresoAlumnoResponse(BaseModel):
    obligatorios_total: int
    aprobados: int
    adeudados: int


class CursadaAlumnoResponse(BaseModel):
    seminario_id: str
    codigo: str
    nombre: str
    horas_catedra: int
    es_obligatorio: bool
    estado: str
    nota_final: Optional[float] = None


class TrabajoFinalAlumnoResponse(BaseModel):
    tipo: str
    titulo: str
    director_nombre: str
    fecha_aprobacion_cpr: Optional[str] = None


class AvanceAlumnoResponse(BaseModel):
    legajo_id: str
    numero_legajo: str
    estado: str
    progreso: ProgresoAlumnoResponse
    seminarios: list[CursadaAlumnoResponse]
    semaforo: str
    trabajo_final: Optional[TrabajoFinalAlumnoResponse] = None
