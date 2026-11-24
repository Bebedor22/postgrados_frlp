"""Contratos del repositorio de seminarios (dominio puro)."""
from typing import Optional

from .entities import CursadaDeLegajo, EstudianteEnSeminario, InscripcionSeminario, ProgresoSeminarios, Seminario


class SeminarioNoEncontrado(LookupError):
    pass


class InscripcionSeminarioNoEncontrada(LookupError):
    pass


class SeminarioRepository:
    """Interfaz de persistencia de seminarios y cursadas."""

    async def crear_seminario(self, seminario: Seminario) -> Seminario:
        raise NotImplementedError("Implementar en infrastructure/pg_repository.py")

    async def obtener_seminario(self, seminario_id: str) -> Optional[Seminario]:
        raise NotImplementedError("Implementar en infrastructure/pg_repository.py")

    async def listar(
            self, carrera_id: Optional[str] = None, solo_obligatorios: bool = False,
            docente_email: Optional[str] = None,
    ) -> list[Seminario]:
        raise NotImplementedError("Implementar en infrastructure/pg_repository.py")

    async def inscribir_estudiante(self, inscripcion: InscripcionSeminario) -> InscripcionSeminario:
        raise NotImplementedError("Implementar en infrastructure/pg_repository.py")

    async def listar_inscritos(self, seminario_id: str) -> list[EstudianteEnSeminario]:
        raise NotImplementedError("Implementar en infrastructure/pg_repository.py")

    async def registrar_nota_final(
            self, legajo_id: str, seminario_id: str, nota: float
    ) -> InscripcionSeminario:
        raise NotImplementedError("Implementar en infrastructure/pg_repository.py")

    async def progreso_obligatorios(self, legajo_id: str) -> ProgresoSeminarios:
        raise NotImplementedError("Implementar en infrastructure/pg_repository.py")

    async def cursadas_de_legajo(self, legajo_id: str) -> list[CursadaDeLegajo]:
        raise NotImplementedError("Implementar en infrastructure/pg_repository.py")
