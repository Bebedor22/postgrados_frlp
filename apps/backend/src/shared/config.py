"""Configuración del backend leída desde variables de entorno.

Ningún secreto vive en el código: se leen de las variables de entorno
(docker-compose las define) o de un archivo `.env` que nunca se sube a Git.
Los valores por defecto sirven solo para desarrollo local y coinciden con
los del docker-compose.yml.
"""
import logging
import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Se busca primero el .env de la raíz del repo y después el de apps/backend
        env_file=("../../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base de datos
    database_url: str = "postgresql+asyncpg://postgrado_user:postgrado_dev_password@localhost:5432/postgrado_dev"

    # JWT — sin valor por defecto fijo: si falta, se genera uno temporal (ver abajo)
    jwt_secret: str = ""
    jwt_algoritmo: str = "HS256"
    jwt_expiracion_minutos: int = 480  # 8 horas

    # CORS: orígenes del frontend separados por coma (Expo web usa el 8081)
    cors_origins: str = "http://localhost:8081,http://localhost:19006"

    # Almacenamiento de PDFs
    storage_path: str = "./storage"
    max_file_size_mb: int = 5

    # Email: "simulado" (solo log) o "smtp" (MailHog en desarrollo)
    email_modo: str = "simulado"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    email_from: str = "noreply@posgrado.frlp.utn.edu.ar"

    # URL del frontend, para armar los links que se envían por email
    frontend_url: str = "http://localhost:8081"

    @property
    def lista_cors_origins(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if not settings.jwt_secret:
        # Sin JWT_SECRET definido, se usa un secreto aleatorio por proceso:
        # funciona para probar, pero los tokens dejan de valer al reiniciar.
        settings.jwt_secret = secrets.token_urlsafe(48)
        logger.warning("JWT_SECRET no está definido: se usa un secreto temporal. Definilo en el .env")
    return settings