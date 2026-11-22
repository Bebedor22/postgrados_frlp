"""Entidades del Módulo B mínimo: seminarios y la cursada de cada legajo.

Solo se modela lo que necesitan los Módulos C y D para calcular el semáforo y
las métricas académicas: qué seminarios son obligatorios y cuáles aprobó cada
estudiante. La planilla de asistencia completa queda fuera de este alcance.
"""
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class EstadoSeminario(Enum):
    CURSANDO = "CURSANDO"
    APROBADO = "APROBADO"
    DESAPROBADO = "DESAPROBADO"


class ReglaAcademicaViolada(Exception):
    """Se intentó registrar un dato académico inválido."""


def validar_nota(valor: float) -> float:
    """Nota final de 1 a 10, con hasta un decimal (RF-DOC-003)."""
    if not 1 <= valor <= 10:
        raise ReglaAcademicaViolada("La nota debe estar entre 1 y 10")
    if round(valor, 1) != valor:
        raise ReglaAcademicaViolada("La nota admite como máximo un decimal")
    return float(valor)


@dataclass
class Seminario:
    id: str
    carrera_id: str
    nombre: str
    codigo: str
    horas_catedra: int
    es_obligatorio: bool = True
    docente_email: Optional[str] = None
    fecha_limite_actas: Optional[date] = None
    actualizado_en: Optional[datetime] = None

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip()
        self.codigo = self.codigo.strip().upper()
        if not self.nombre or not self.codigo:
            raise ReglaAcademicaViolada("El nombre y el código del seminario son obligatorios")
        if self.horas_catedra < 0:
            raise ReglaAcademicaViolada("Las horas cátedra no pueden ser negativas")


@dataclass
class InscripcionSeminario:
    id: str
    legajo_id: str
    seminario_id: str
    nota_final: Optional[float] = None
    asistencias: int = 0
    total_clases: int = 0
    estado: EstadoSeminario = EstadoSeminario.CURSANDO

    def __post_init__(self) -> None:
        if self.asistencias < 0 or self.total_clases < 0:
            raise ReglaAcademicaViolada("Las asistencias no pueden ser negativas")
        if self.nota_final is not None:
            self.nota_final = validar_nota(self.nota_final)
        if self.estado == EstadoSeminario.APROBADO and self.nota_final is None:
            raise ReglaAcademicaViolada("Un seminario aprobado necesita nota final")

    def registrar_nota(self, nota: float) -> "InscripcionSeminario":
        """BR-003: con nota >= 4 el seminario queda aprobado; si no, desaprobado."""
        self.nota_final = validar_nota(nota)
        self.estado = EstadoSeminario.APROBADO if nota >= 4 else EstadoSeminario.DESAPROBADO
        return self


@dataclass(frozen=True)
class ProgresoSeminarios:
    """Avance del estudiante en los seminarios obligatorios de su carrera."""

    obligatorios_total: int
    aprobados: int

    @property
    def adeudados(self) -> int:
        return max(self.obligatorios_total - self.aprobados, 0)


@dataclass(frozen=True)
class CursadaDeLegajo:
    """Un seminario y el resultado que obtuvo un legajo en él (portal del alumno)."""

    seminario_id: str
    codigo: str
    nombre: str
    horas_catedra: int
    es_obligatorio: bool
    estado: EstadoSeminario
    nota_final: Optional[float] = None


@dataclass(frozen=True)
class EstudianteEnSeminario:
    """Fila del listado de inscriptos a un seminario (con los datos del legajo)."""

    legajo_id: str
    numero_legajo: str
    apellido: str
    nombre: str
    email: str
    nota_final: Optional[float] = None
    estado: EstadoSeminario = EstadoSeminario.CURSANDO
