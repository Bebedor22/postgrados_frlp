"""Modelos SQLAlchemy de la oferta académica."""
import uuid
from datetime import datetime

from sqlalchemy import UUID, Boolean, CheckConstraint, Column, Date, DateTime, Integer, String

from src.shared.database.connection import Base


class CarreraModel(Base):
    __tablename__ = "carreras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(150), nullable=False, unique=True)
    tipo = Column(String(30), nullable=False)
    duracion_anios = Column(Integer, nullable=False)
    activa = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        CheckConstraint("tipo IN ('Especializacion','Maestria','Doctorado')", name="tipo_carrera_valido"),
        CheckConstraint("duracion_anios BETWEEN 1 AND 6", name="duracion_valida"),
    )


class CohorteModel(Base):
    __tablename__ = "cohortes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    anio = Column(Integer, nullable=False)
    nombre = Column(String(50), nullable=False, unique=True)
    abierta = Column(Boolean, nullable=False, default=False)
    fecha_inicio = Column(Date)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<Cohorte {self.nombre} ({self.anio})>"