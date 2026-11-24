"""Esquemas Pydantic del Módulo C."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TrabajoFinalCreate(BaseModel):
    tipo: str = Field(..., description="TFI o TESIS")
    titulo: str = Field(..., min_length=3, max_length=300)
    director_nombre: str = Field(..., min_length=1, max_length=150)
    director_email: str = Field(..., max_length=255)
    codirector_nombre: Optional[str] = Field(None, max_length=150)
    fecha_aprobacion_cpr: Optional[date] = None
    numero_resolucion: Optional[str] = None

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if valor not in ("TFI", "TESIS"):
            raise ValueError("El tipo debe ser TFI o TESIS")
        return valor


class TrabajoFinalUpdate(BaseModel):
    tipo: Optional[str] = None
    titulo: Optional[str] = Field(None, min_length=3, max_length=300)
    director_nombre: Optional[str] = Field(None, min_length=1, max_length=150)
    director_email: Optional[str] = Field(None, max_length=255)
    codirector_nombre: Optional[str] = Field(None, max_length=150)
    fecha_aprobacion_cpr: Optional[date] = None
    numero_resolucion: Optional[str] = None
    limpiar_fecha_cpr: bool = Field(False, description="True para quitar la fecha de aprobación CPR")

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return None
        valor = valor.strip().upper()
        if valor not in ("TFI", "TESIS"):
            raise ValueError("El tipo debe ser TFI o TESIS")
        return valor


class TrabajoFinalResponse(BaseModel):
    id: str
    legajo_id: str
    tipo: str
    titulo: str
    director_nombre: str
    director_email: str
    codirector_nombre: Optional[str] = None
    fecha_aprobacion_cpr: Optional[date] = None
    numero_resolucion: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SemaforoResponse(BaseModel):
    legajo_id: str
    numero_legajo: str
    apellido: str
    nombre: str
    carrera: str
    tipo_carrera: str
    fecha_inscripcion: Optional[date] = None
    semaforo: str
    semaforo_manual: bool
    semaforo_desde: Optional[datetime] = None
    dias_en_riesgo: int
    seminarios_obligatorios_total: int
    seminarios_aprobados: int
    seminarios_adeudados: int
    tiene_tfi_registrado: bool
    tiene_fecha_cpr: bool


class EnRiesgoResponse(BaseModel):
    total: int
    legajos: list[SemaforoResponse]


class SemaforoManualRequest(BaseModel):
    manual: bool = Field(True, description="True fija VERDE; False restaura el cálculo automático")


class LegajoTesisItem(BaseModel):
    """Búsqueda reducida para que CPR pueda dar de alta un TFI sin ver la bandeja completa."""

    legajo_id: str
    numero_legajo: str
    apellido: str
    nombre: str
    carrera: str
    estado: str
    tiene_trabajo_final: bool
