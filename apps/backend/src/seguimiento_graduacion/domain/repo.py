"""Interfaces de persistencia y filas de lectura del Módulo C."""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from .semaforo import DatosSemaforo
from .trabajo_final import TrabajoFinal


class TrabajoFinalRepository:
    async def crear(self, trabajo: TrabajoFinal) -> TrabajoFinal:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener_por_id(self, trabajo_id: str) -> Optional[TrabajoFinal]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener_por_legajo(self, legajo_id: str) -> Optional[TrabajoFinal]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def actualizar(self, trabajo: TrabajoFinal) -> TrabajoFinal:
        raise NotImplementedError("Implementar en pg_repository.py")


@dataclass
class FilaSeguimiento:
    """Legajo activo con todo lo que muestra el dashboard del coordinador."""

    legajo_id: str
    numero_legajo: str
    apellido: str
    nombre: str
    carrera_nombre: str
    tipo_carrera: str
    fecha_inscripcion: Optional[date]
    semaforo: str
    semaforo_manual: bool
    semaforo_desde: Optional[datetime]
    seminarios_obligatorios_total: int
    seminarios_aprobados: int
    tiene_tfi_registrado: bool
    tiene_fecha_cpr: bool

    @property
    def seminarios_adeudados(self) -> int:
        return max(self.seminarios_obligatorios_total - self.seminarios_aprobados, 0)

    def dias_en_riesgo(self, hoy: Optional[date] = None) -> int:
        if self.semaforo_desde is None:
            return 0
        return max(((hoy or date.today()) - self.semaforo_desde.date()).days, 0)


class SeguimientoRepository:
    async def datos_de_legajo(self, legajo_id: str) -> Optional[DatosSemaforo]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def legajos_activos_ids(self) -> list[str]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def guardar_semaforo(self, legajo_id: str, estado: str, fecha: datetime) -> bool:
        """Actualiza el semáforo automático; devuelve False si lo pisó un VERDE manual."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def marcar_verde_manual(self, legajo_id: str, fecha: datetime) -> None:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def limpiar_semaforo_manual(self, legajo_id: str, fecha: datetime) -> None:
        """Quita el override manual para que vuelva a regir el cálculo automático."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener_fila(self, legajo_id: str) -> Optional[FilaSeguimiento]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def listar_en_riesgo(self) -> list[FilaSeguimiento]:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def listar_activos(self) -> list[FilaSeguimiento]:
        raise NotImplementedError("Implementar en pg_repository.py")
