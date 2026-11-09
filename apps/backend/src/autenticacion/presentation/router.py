from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.autenticacion.application.iniciar_sesion import CredencialesInvalidas, iniciar_sesion
from src.autenticacion.infrastructure.bcrypt_hasher import BcryptHasher
from src.autenticacion.infrastructure.pg_repository import PostgresUsuarioRepository
from src.autenticacion.presentation.schemas import LoginRequest, TokenResponse, UsuarioResponse
from src.shared.auth.dependencies import get_usuario_autenticado
from src.shared.auth.jwt import ACCESS_TOKEN_EXPIRE_MINUTES, generar_token
from src.shared.database.connection import get_db

router = APIRouter()


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Recibe email y contraseña y devuelve un JWT válido por 8 horas.",
)
async def login(datos: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        usuario = await iniciar_sesion(
            email=datos.email,
            contrasena=datos.password,
            repo=PostgresUsuarioRepository(db),
            hasher=BcryptHasher(),
        )
    except CredencialesInvalidas:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    token = generar_token(
        {"sub": usuario.id, "email": usuario.email, "nombre": usuario.nombre, "rol": usuario.rol.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        usuario=UsuarioResponse(id=usuario.id, email=usuario.email, nombre=usuario.nombre, rol=usuario.rol.value),
    )


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Usuario de la sesión actual",
    description="Devuelve los datos del usuario dueño del token. Sirve al frontend para saber el rol.",
)
async def usuario_actual(payload: dict = Depends(get_usuario_autenticado)) -> UsuarioResponse:
    return UsuarioResponse(
        id=payload["sub"], email=payload["email"], nombre=payload.get("nombre", ""), rol=payload["rol"]
    )