"""Esquemas Pydantic del Módulo B (seminarios y cursadas)."""
import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SeminarioCrear(BaseModel):
    carrera_id: str
    nombre: str = Field(..., min_length=1, max_length=150)
    codigo: str = Field(..., min_length=1, max_length=50)
    horas_catedra: int = Field(..., ge=0)
    es_obligatorio: bool = True
    docente_email: Optional[str] = Field(None, max_length=255)
    fecha_limite_actas: Optional[date] = None

    @field_validator("docente_email")
    @classmethod
    def _email_del_docente(cls, valor: Optional[str]) -> Optional[str]:
        """En minúsculas, como el email del login: si no, el docente no ve su seminario."""
        if valor is None or not valor.strip():
            return None
        valor = valor.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
            raise ValueError("El email del docente no es válido")
        return valor


class SeminarioResponse(BaseModel):
    id: str
    carrera_id: str
    nombre: str
    codigo: str
    horas_catedra: int
    es_obligatorio: bool
    docente_email: Optional[str] = None
    fecha_limite_actas: Optional[date] = None


class EstudianteInscripcion(BaseModel):
    legajo_id: str


class InscripcionResponse(BaseModel):
    id: str
    legajo_id: str
    seminario_id: str
    nota_final: Optional[float] = None
    estado: str


class NotaFinal(BaseModel):
    legajo_id: str
    nota: float = Field(..., ge=1, le=10, description="Nota final de 1 a 10, con un decimal")


class NotasFinales(BaseModel):
    notas: list[NotaFinal] = Field(..., min_length=1, max_length=500)


class EstudianteSeminarioResponse(BaseModel):
    legajo_id: str
    numero_legajo: str
    apellido: str
    nombre: str
    email: str
    nota_final: Optional[float] = None
    estado: str


class ProgresoResponse(BaseModel):
    obligatorios_total: int
    aprobados: int
    adeudados: int
