from datetime import datetime
from typing import Optional

from dataclasses import dataclass

from .entities import CambioDeEstado, EstadoLegajo, Legajo
from .formulario import FormularioInscripcion


@dataclass
class FiltrosLegajos:
    """Criterios de búsqueda de la bandeja del coordinador."""

    cohorte_id: Optional[str] = None
    carrera_id: Optional[str] = None
    estado: Optional[EstadoLegajo] = None
    texto: Optional[str] = None  # apellido, nombre, documento o email
    pagina: int = 1
    por_pagina: int = 20


class LegajoRepository:
    """Interfaz abstracta para el repositorio de legajos.
    
    La implementación concreta vive en infrastructure/ (usa SQLAlchemy).
    Esta interfaz define el contrato que la capa de aplicación depende.
    Ningún otro módulo debe importar de SQLAlchemy directamente.
    """

    async def guardar(self, legajo: Legajo) -> Legajo:
        """Guardar un legajo en la base de datos. Debe implementarse en infrastructure/pg_repository.py."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener_por_dni(self, dni: str) -> Optional[Legajo]:
        """Obtener un legajo por su DNI. Único en cohorte activa."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener_por_id(self, legajo_id: str) -> Optional[Legajo]:
        """Obtener un legajo por su ID."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def listar_por_cohorte_y_estado(
            self, cohorte_id: str, estado: EstadoLegajo
    ) -> list[Legajo]:
        """Listar legajos de una cohorte con un estado específico."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def listar_en_estado(self, estado: EstadoLegajo) -> list[Legajo]:
        """Listar todos los legajos en un estado dado."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def actualizar_estado(
            self,
            legajo_id: str,
            nuevo_estado: EstadoLegajo,
            comentario: Optional[str] = None,
            usuario_email: Optional[str] = None,
    ) -> Legajo:
        """Actualizar el estado de un legajo y registrar en auditoría."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def existe_dni_en_cohorte(self, dni: str, cohorte_id: str) -> bool:
        """Verificar si ya existe un aspirante con ese DNI en la cohorte."""
        raise NotImplementedError("Implementar en pg_repository.py")

    # ── Inscripción por pasos ────────────────────────────────────────────────

    async def crear_inscripcion(
            self, legajo: Legajo, formulario: FormularioInscripcion, token_hash: str
    ) -> Legajo:
        """Crear el legajo en BORRADOR junto con su formulario y su token de seguimiento."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener_por_token(self, token_hash: str) -> Optional[Legajo]:
        """Buscar el legajo dueño de un token de seguimiento (se guarda solo el hash)."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def obtener_formulario(self, legajo_id: str) -> FormularioInscripcion:
        """Datos del formulario de inscripción de un legajo."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def guardar_formulario(self, legajo_id: str, formulario: FormularioInscripcion) -> None:
        """Guardar el formulario (guardado parcial del aspirante)."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def registrar_confirmacion(self, legajo_id: str, fecha: datetime) -> None:
        """Guardar la fecha en que el aspirante envió la inscripción."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def contar_inscripciones_vigentes(self, numero_documento: str, cohorte_id: str) -> int:
        """Cantidad de carreras en las que el documento está inscripto en la cohorte (BR-001)."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def existe_inscripcion(self, numero_documento: str, cohorte_id: str, carrera_id: str) -> bool:
        """Si el documento ya tiene una inscripción a esa carrera en esa cohorte."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def historial(self, legajo_id: str) -> list[CambioDeEstado]:
        """Cambios de estado del legajo, del más viejo al más nuevo."""
        raise NotImplementedError("Implementar en pg_repository.py")

    # ── Bandeja y workflow del coordinador ───────────────────────────────────

    async def buscar(self, filtros: FiltrosLegajos) -> tuple[list[Legajo], int]:
        """Legajos que cumplen los filtros (una página) y el total sin paginar."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def contar_por_estado(self, cohorte_id: Optional[str] = None) -> dict[str, int]:
        """Cantidad de legajos en cada estado (opcionalmente de una cohorte)."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def siguiente_secuencial(self, prefijo: str) -> int:
        """Próximo número libre para los legajos definitivos que empiezan con el prefijo."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def asignar_numero(self, legajo_id: str, numero_legajo: str) -> None:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def registrar_activacion(self, legajo_id: str, fecha: datetime) -> None:
        raise NotImplementedError("Implementar en pg_repository.py")

    async def fecha_de_estado(self, legajo_id: str, estado: EstadoLegajo) -> Optional[datetime]:
        """Última fecha en que el legajo entró al estado indicado (según la auditoría)."""
        raise NotImplementedError("Implementar en pg_repository.py")

    async def listar_en_estado_desde_antes_de(self, estado: EstadoLegajo, limite: datetime) -> list[Legajo]:
        """Legajos que siguen en `estado` y entraron a él antes de `limite` (para BR-005)."""
        raise NotImplementedError("Implementar en pg_repository.py")