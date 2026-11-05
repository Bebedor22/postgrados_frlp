from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.shared.config import get_settings

# La URL viene de la variable de entorno DATABASE_URL (ver src/shared/config.py).
# Formato: postgresql+asyncpg://usuario:password@host:puerto/base
DATABASE_URL = get_settings().database_url

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Session maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base para modelos SQLAlchemy
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency que provee una sesión de base de datos.

    Confirma (commit) la transacción si el endpoint terminó bien y la
    deshace (rollback) si se lanzó una excepción.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def crear_todas_las_tablas():
    """Crear todas las tablas definidas en los modelos Base."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def borrar_todas_las_tablas():
    """Eliminar todas las tablas (útil para testing)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
