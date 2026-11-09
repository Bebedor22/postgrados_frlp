"""Interfaces (puertos) que necesita la capa de aplicación.

Las implementaciones concretas viven en infrastructure/.
"""
from typing import Optional, Protocol

from .entities import Usuario


class UsuarioRepository(Protocol):
    async def obtener_por_email(self, email: str) -> Optional[Usuario]: ...

    async def guardar(self, usuario: Usuario) -> Usuario: ...


class HasherContrasenas(Protocol):
    """Calcula y verifica hashes de contraseñas (bcrypt en infraestructura)."""

    def hashear(self, contrasena: str) -> str: ...

    def verificar(self, contrasena: str, password_hash: str) -> bool: ...