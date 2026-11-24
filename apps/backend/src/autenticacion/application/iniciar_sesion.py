"""Caso de uso: iniciar sesión con email y contraseña."""
from src.autenticacion.domain.entities import Usuario
from src.autenticacion.domain.repo import HasherContrasenas, UsuarioRepository


class CredencialesInvalidas(Exception):
    """Email inexistente, contraseña incorrecta o usuario inactivo.

    Se usa un único error para los tres casos, así no se revela qué emails existen.
    """


async def iniciar_sesion(
        email: str,
        contrasena: str,
        repo: UsuarioRepository,
        hasher: HasherContrasenas,
) -> Usuario:
    usuario = await repo.obtener_por_email(email.strip().lower())
    if usuario is None or not usuario.puede_iniciar_sesion():
        raise CredencialesInvalidas()
    if not hasher.verificar(contrasena, usuario.password_hash):
        raise CredencialesInvalidas()
    return usuario