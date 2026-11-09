"""Entidades de la oferta académica: carreras y cohortes (sin frameworks)."""
from dataclasses import dataclass
from datetime import date
from typing import Optional

TIPOS_DE_CARRERA = ("Especializacion", "Maestria", "Doctorado")


class ReglaDeNegocioViolada(Exception):
    """Se intentó una operación que el dominio no permite."""


@dataclass
class Carrera:
    id: str
    nombre: str
    tipo: str  # Especializacion | Maestria | Doctorado
    duracion_anios: int
    activa: bool = True

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip()
        if not self.nombre:
            raise ReglaDeNegocioViolada("El nombre de la carrera es obligatorio")
        if self.tipo not in TIPOS_DE_CARRERA:
            raise ReglaDeNegocioViolada(f"Tipo de carrera inválido. Opciones: {', '.join(TIPOS_DE_CARRERA)}")
        if not 1 <= self.duracion_anios <= 6:
            raise ReglaDeNegocioViolada("La duración debe estar entre 1 y 6 años")


@dataclass
class Cohorte:
    id: str
    anio: int
    nombre: str
    inscripcion_abierta: bool = False
    fecha_inicio: Optional[date] = None

    def abrir_inscripcion(self) -> None:
        """BR-009: el período de inscripción solo lo abre el coordinador."""
        if self.inscripcion_abierta:
            raise ReglaDeNegocioViolada(f"La inscripción de {self.nombre} ya está abierta")
        self.inscripcion_abierta = True

    def cerrar_inscripcion(self) -> None:
        """BR-009: el período de inscripción solo lo cierra el coordinador."""
        if not self.inscripcion_abierta:
            raise ReglaDeNegocioViolada(f"La inscripción de {self.nombre} ya está cerrada")
        self.inscripcion_abierta = False

    def acepta_inscripciones(self) -> bool:
        return self.inscripcion_abierta