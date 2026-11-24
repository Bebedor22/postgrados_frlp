"""Entidad del trabajo final / tesis (RF-GRAD-001)."""
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class TipoTrabajoFinal(Enum):
    TFI = "TFI"
    TESIS = "TESIS"


class ReglaTrabajoFinalViolada(Exception):
    """Datos del trabajo final inválidos."""


class LegajoNoActivo(ReglaTrabajoFinalViolada):
    """Se intentó registrar un trabajo final en un legajo que no está ACTIVO."""


@dataclass
class TrabajoFinal:
    id: str
    legajo_id: str
    tipo: TipoTrabajoFinal
    titulo: str
    director_nombre: str
    director_email: str
    codirector_nombre: Optional[str] = None
    fecha_aprobacion_cpr: Optional[date] = None
    numero_resolucion: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if isinstance(self.tipo, str):
            try:
                self.tipo = TipoTrabajoFinal(self.tipo)
            except ValueError as error:
                raise ReglaTrabajoFinalViolada("El tipo debe ser TFI o TESIS") from error
        self.titulo = self.titulo.strip()
        self.director_nombre = self.director_nombre.strip()
        self.codirector_nombre = (self.codirector_nombre or "").strip() or None
        self.numero_resolucion = (self.numero_resolucion or "").strip() or None
        if len(self.titulo) < 3:
            raise ReglaTrabajoFinalViolada("El título debe tener al menos 3 caracteres")
        if not self.director_nombre:
            raise ReglaTrabajoFinalViolada("El director es obligatorio")
        if self.fecha_aprobacion_cpr and self.fecha_aprobacion_cpr > date.today():
            raise ReglaTrabajoFinalViolada("La fecha de aprobación de CPR no puede ser futura")
        if "@" not in self.director_email or self.director_email.startswith("@") \
                or self.director_email.endswith("@"):
            raise ReglaTrabajoFinalViolada("El email del director no es válido")

    def aprobado_por_cpr(self) -> bool:
        return self.fecha_aprobacion_cpr is not None
