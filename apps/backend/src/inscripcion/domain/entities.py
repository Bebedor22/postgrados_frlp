from dataclasses import dataclass
from enum import Enum
from datetime import date, timedelta
from typing import Optional


class EstadoLegajo(Enum):
    BORRADOR = "BORRADOR"
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    OBSERVADO = "OBSERVADO"
    COMPLETADO = "COMPLETADO"
    ACTIVO = "ACTIVO"
    VENCIDO = "VENCIDO"
    RECHAZADO = "RECHAZADO"
    BAJA = "BAJA"
    GRADUADO = "GRADUADO"


class TransicionInvalida(Exception):
    """Se intentó un cambio de estado que el workflow no permite."""


# Workflow del legajo (ARQUITECTURA.md §6). Un estado sin salidas es terminal.
TRANSICIONES_PERMITIDAS: dict[EstadoLegajo, set[EstadoLegajo]] = {
    EstadoLegajo.BORRADOR: {EstadoLegajo.PENDIENTE},
    EstadoLegajo.PENDIENTE: {EstadoLegajo.EN_REVISION, EstadoLegajo.OBSERVADO},
    EstadoLegajo.EN_REVISION: {EstadoLegajo.COMPLETADO, EstadoLegajo.OBSERVADO, EstadoLegajo.RECHAZADO},
    EstadoLegajo.OBSERVADO: {EstadoLegajo.PENDIENTE},
    EstadoLegajo.COMPLETADO: {EstadoLegajo.ACTIVO, EstadoLegajo.VENCIDO, EstadoLegajo.BAJA},
    EstadoLegajo.ACTIVO: {EstadoLegajo.GRADUADO, EstadoLegajo.BAJA},
    EstadoLegajo.VENCIDO: set(),
    EstadoLegajo.RECHAZADO: set(),
    EstadoLegajo.BAJA: set(),
    EstadoLegajo.GRADUADO: set(),
}

DIAS_RESERVA_VACANTE = 30  # BR-005

def prefijo_de_legajo(anio_cohorte: int, numero_cohorte: int) -> str:
    """Parte fija del número de legajo de una cohorte: "26-001-"."""
    return f"{anio_cohorte % 100:02d}-{numero_cohorte:03d}-"


def numero_de_legajo(anio_cohorte: int, numero_cohorte: int, secuencial: int) -> str:
    """Formato del SRS (RF-CORE-003): AÑO-COHORTE-SECUENCIAL.

    Ejemplo: "26-001-045" → año 2026, cohorte 1, estudiante 45.
    """
    return f"{prefijo_de_legajo(anio_cohorte, numero_cohorte)}{secuencial:03d}"


@dataclass
class Aspirante:
    id: str
    dni: "DNI"
    email: "Email"
    nombre: str
    apellido: str
    tipo_carrera: "TipoCarrera"
    carrera_elegida: str
    motivacion: str
    solicita_beca: bool
    estado: EstadoLegajo = EstadoLegajo.BORRADOR
    fecha_inscripcion: Optional[date] = None

    def cambiar_estado(self, nuevo_estado: EstadoLegajo) -> "Aspirante":
        self.estado = nuevo_estado
        return self

@dataclass
class CambioDeEstado:
    """Un registro del historial de estados de un legajo (tabla auditoria_legajos)."""

    estado_anterior: Optional[str]
    estado_nuevo: str
    comentario: Optional[str]
    fecha: date

@dataclass
class Legajo:
    id: str
    numero_legajo: str  # Formato: AÑO-COHORTE-SECUENCIAL (ej: 26-001-045)
    cohorte_id: str
    dni: "DNI"
    apellido: str
    nombre: str
    email: "Email"
    tipo_carrera: "TipoCarrera"
    solicita_beca: bool
    tipo_beca: Optional[str] = None
    estado: EstadoLegajo = EstadoLegajo.BORRADOR
    fecha_inscripcion: Optional[date] = None
    fecha_activacion: Optional[date] = None
    semaforo: str = "VERDE"
    semaforo_manual: bool = False
    carrera_id: Optional[str] = None
    tipo_documento: str = "DNI"

    def puede_editar_formulario(self) -> bool:
        """El aspirante solo modifica su formulario en BORRADOR u OBSERVADO."""
        return self.estado in (EstadoLegajo.BORRADOR, EstadoLegajo.OBSERVADO)

    def puede_transicionar_a(self, nuevo_estado: EstadoLegajo) -> bool:
        """Reglas del workflow del legajo (ver TRANSICIONES_PERMITIDAS)."""
        return nuevo_estado in TRANSICIONES_PERMITIDAS[self.estado]

    def transicionar_a(self, nuevo_estado: EstadoLegajo) -> None:
        if not self.puede_transicionar_a(nuevo_estado):
            raise TransicionInvalida(
                f"No se puede pasar de {self.estado.value} a {nuevo_estado.value}"
            )
        self.estado = nuevo_estado

    @staticmethod
    def vencimiento_de_reserva(fecha_completado: date) -> date:
        """BR-005: la reserva de vacante vence a los 30 días corridos desde COMPLETADO."""
        return fecha_completado + timedelta(days=DIAS_RESERVA_VACANTE)

    def es_estado_terminal(self) -> bool:
        """Un estado es terminal si no puede seguir transicionando."""
        return not TRANSICIONES_PERMITIDAS[self.estado]


@dataclass
class TipoCarrera:
    valor: str

    def __str__(self) -> str:
        return self.valor


# Alias para compatibilidad con esquemas Pydantic/BD
Esp = TipoCarrera("Especializacion")
Maestria = TipoCarrera("Maestria")
Doctorado = TipoCarrera("Doctorado")