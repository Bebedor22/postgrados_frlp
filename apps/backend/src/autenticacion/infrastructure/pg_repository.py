import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.autenticacion.domain.entities import Rol, Usuario
from src.autenticacion.infrastructure.orm_models import UsuarioModel


class PostgresUsuarioRepository:
    """Implementación de UsuarioRepository con SQLAlchemy async."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def obtener_por_email(self, email: str) -> Optional[Usuario]:
        result = await self._session.execute(select(UsuarioModel).where(UsuarioModel.email == email))
        modelo = result.scalar_one_or_none()
        return self._a_dominio(modelo) if modelo else None

    async def guardar(self, usuario: Usuario) -> Usuario:
        modelo = UsuarioModel(
            id=uuid.UUID(usuario.id),
            email=usuario.email,
            password_hash=usuario.password_hash,
            nombre=usuario.nombre,
            rol=usuario.rol.value,
            activo=usuario.activo,
        )
        self._session.add(modelo)
        await self._session.flush()
        return usuario

    @staticmethod
    def _a_dominio(modelo: UsuarioModel) -> Usuario:
        return Usuario(
            id=str(modelo.id),
            email=modelo.email,
            nombre=modelo.nombre,
            rol=Rol(modelo.rol),
            password_hash=modelo.password_hash,
            activo=modelo.activo,
        )