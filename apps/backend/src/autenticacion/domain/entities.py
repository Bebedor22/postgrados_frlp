"""Entidades del dominio de autenticación (sin imports de frameworks)."""
from dataclasses import dataclass
from enum import Enum


class Rol(Enum):
    """Roles del sistema (ARQUITECTURA.md §7.2 + pedido de la Secretaría de Posgrado)."""

    ASPIRANTE = "ASPIRANTE"
    DOCENTE = "DOCENTE"
    COORDINADOR = "COORDINADOR"  # Equipo de conducción de la carrera
    CPR = "CPR"  # Comisión de Posgrado Regional
    DIRECCION = "DIRECCION"  # Dirección de Posgrado
    ADMIN = "ADMIN"


@dataclass
class Usuario:
    id: str
    email: str
    nombre: str
    rol: Rol
    password_hash: str
    activo: bool = True

    def puede_iniciar_sesion(self) -> bool:
        """Solo los usuarios activos pueden iniciar sesión."""
        return self.activo