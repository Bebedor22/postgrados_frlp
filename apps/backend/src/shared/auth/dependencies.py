"""Dependencias de FastAPI para autenticación y autorización por rol.

Uso en un endpoint (ARQUITECTURA.md §7.3):
    @router.get("/legajos", dependencies=[Depends(require_role("COORDINADOR"))])
"""
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.shared.auth.jwt import decodificar_token

security = HTTPBearer(auto_error=False)


def _error_401(mensaje: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=mensaje,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """Usuario actual desde el JWT, o None si no se envió token (endpoints públicos)."""
    if credentials is None:
        return None
    try:
        return decodificar_token(credentials.credentials)
    except ValueError as error:
        raise _error_401(str(error))


async def get_usuario_autenticado(
        usuario: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Igual que get_current_user, pero exige que haya token."""
    if usuario is None:
        raise _error_401("Credenciales requeridas")
    return usuario


def require_role(*roles: str):
    """Dependency que exige un token válido con alguno de los roles indicados."""

    async def dependency(usuario: Dict[str, Any] = Depends(get_usuario_autenticado)) -> Dict[str, Any]:
        if usuario.get("rol") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol requerido: {' o '.join(roles)}. Tu rol: {usuario.get('rol')}",
            )
        return usuario

    return dependency


# Atajos por rol (se mantienen por compatibilidad con los routers existentes)
def require_role_coordinador():
    return require_role("COORDINADOR")


def require_role_docente():
    return require_role("DOCENTE")


def require_role_cpr():
    return require_role("CPR")


def require_role_aspirante():
    return require_role("ASPIRANTE")