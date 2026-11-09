"""Crea los usuarios de prueba del sistema (solo para desarrollo).

Uso (con Docker levantado, desde la raíz del repo):
    docker compose exec backend python -m scripts.crear_usuarios_iniciales

Es idempotente: si un usuario ya existe, lo saltea. Las credenciales son las
de docs/SEED_DATA.json y NO deben usarse en producción.
"""
import asyncio

from src.autenticacion.application.registrar_usuario import UsuarioYaExiste, registrar_usuario
from src.autenticacion.domain.entities import Rol
from src.autenticacion.infrastructure.bcrypt_hasher import BcryptHasher
from src.autenticacion.infrastructure.pg_repository import PostgresUsuarioRepository
from src.shared.database.connection import AsyncSessionLocal, engine

USUARIOS_DE_PRUEBA = [
    ("admin@fenix.test", "María González", Rol.COORDINADOR, "Admin1234!"),
    ("docente@fenix.test", "Carlos Pérez", Rol.DOCENTE, "Docente1234!"),
    ("cpr@fenix.test", "Laura Martínez", Rol.CPR, "Cpr1234!"),
    ("direccion@fenix.test", "Jorge Ramírez", Rol.DIRECCION, "Direccion1234!"),
]


async def main() -> None:
    hasher = BcryptHasher()
    async with AsyncSessionLocal() as session:
        repo = PostgresUsuarioRepository(session)
        for email, nombre, rol, contrasena in USUARIOS_DE_PRUEBA:
            try:
                await registrar_usuario(email, nombre, rol, contrasena, repo, hasher)
                print(f"✔ Creado {email} ({rol.value})")
            except UsuarioYaExiste:
                print(f"• Ya existía {email}, se saltea")
        await session.commit()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())