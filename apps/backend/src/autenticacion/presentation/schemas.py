"""Esquemas Pydantic (request/response) de autenticación."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    # Sin validar formato: si el email no existe, el login responde 401 igual
    email: str = Field(min_length=3, max_length=255, examples=["admin@fenix.test"])
    password: str = Field(min_length=1, max_length=128, examples=["Admin1234!"])


class UsuarioResponse(BaseModel):
    id: str
    email: str
    nombre: str
    rol: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos
    usuario: UsuarioResponse