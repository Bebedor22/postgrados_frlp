"""Modelo SQLAlchemy de usuarios del sistema."""
import uuid
from datetime import datetime

from sqlalchemy import UUID, Boolean, CheckConstraint, Column, DateTime, String

from src.shared.database.connection import Base


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(150), nullable=False)
    rol = Column(String(20), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        CheckConstraint(
            "rol IN ('ASPIRANTE','DOCENTE','COORDINADOR','CPR','DIRECCION','ADMIN')",
            name="rol_valido",
        ),
    )