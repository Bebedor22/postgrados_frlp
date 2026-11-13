"""Caso de uso: dar de alta un usuario del sistema (coordinador, docente, CPR)."""
import uuid

from src.autenticacion.domain.entities import Rol, Usuario
from src.autenticacion.domain.repo import HasherContrasenas, UsuarioRepository

LARGO_MINIMO_CONTRASENA = 8


class UsuarioYaExiste(Exception):
    pass


async def registrar_usuario(
        email: str,
        nombre: str,
        rol: Rol,
        contrasena: str,
        repo: UsuarioRepository,
        hasher: HasherContrasenas,
) -> Usuario:
    if len(contrasena) < LARGO_MINIMO_CONTRASENA:
        raise ValueError(f"La contraseña debe tener al menos {LARGO_MINIMO_CONTRASENA} caracteres")

    email_normalizado = email.strip().lower()
    if await repo.obtener_por_email(email_normalizado) is not None:
        raise UsuarioYaExiste(email_normalizado)

    usuario = Usuario(
        id=str(uuid.uuid4()),
        email=email_normalizado,
        nombre=nombre,
        rol=rol,
        password_hash=hasher.hashear(contrasena),
    )
    return await repo.guardar(usuario)