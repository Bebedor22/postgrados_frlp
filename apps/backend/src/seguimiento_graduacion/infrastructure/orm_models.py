"""Modelo SQLAlchemy del trabajo final / tesis (Módulo C)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)

from src.shared.database.connection import Base


class TrabajoFinalModel(Base):
    __tablename__ = "trabajos_finales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legajo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("legajos.id", ondelete="CASCADE", name="fk_trabajos_finales_legajo"),
        nullable=False,
    )
    tipo = Column(String(10), nullable=False)
    titulo = Column(String(300), nullable=False)
    director_nombre = Column(String(150), nullable=False)
    director_email = Column(String(255), nullable=False)
    codirector_nombre = Column(String(150), nullable=True)
    fecha_aprobacion_cpr = Column(Date, nullable=True)
    numero_resolucion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        CheckConstraint("tipo IN ('TFI','TESIS')", name="tipo_trabajo_final_valido"),
        UniqueConstraint("legajo_id", name="uq_trabajo_final_por_legajo"),
    )

    def __repr__(self) -> str:
        return f"<TrabajoFinal {self.tipo} - {self.titulo[:30]}>"
