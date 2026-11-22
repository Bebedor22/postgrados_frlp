"""Modelos SQLAlchemy del Módulo B mínimo (seminarios y cursadas)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from src.shared.database.connection import Base


class SeminarioModel(Base):
    __tablename__ = "seminarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    carrera_id = Column(
        UUID(as_uuid=True),
        ForeignKey("carreras.id", ondelete="CASCADE", name="fk_seminarios_carrera"),
        nullable=False,
    )
    nombre = Column(String(150), nullable=False)
    codigo = Column(String(50), nullable=False, unique=True)
    horas_catedra = Column(Integer, nullable=False, default=0)
    es_obligatorio = Column(Boolean, nullable=False, default=True)
    docente_email = Column(String(255), nullable=True)
    fecha_limite_actas = Column(Date, nullable=True)
    actualizado_en = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

    inscripciones = relationship("InscripcionSeminarioModel", back_populates="seminario")

    __table_args__ = (
        CheckConstraint("horas_catedra >= 0", name="horas_catedra_validas"),
        Index("idx_seminarios_carrera", "carrera_id"),
    )

    def __repr__(self) -> str:
        return f"<Seminario {self.codigo} - {self.nombre}>"


class InscripcionSeminarioModel(Base):
    __tablename__ = "inscripcion_seminario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legajo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("legajos.id", ondelete="CASCADE", name="fk_inscripcion_seminario_legajo"),
        nullable=False,
    )
    seminario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("seminarios.id", ondelete="CASCADE", name="fk_inscripcion_seminario_seminario"),
        nullable=False,
    )
    nota_final = Column(Numeric(3, 1), nullable=True)
    asistencias = Column(Integer, nullable=False, default=0)
    total_clases = Column(Integer, nullable=False, default=0)
    estado = Column(String(20), nullable=False, default="CURSANDO")
    actualizado_en = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    seminario = relationship("SeminarioModel", back_populates="inscripciones")

    __table_args__ = (
        CheckConstraint(
            "estado IN ('CURSANDO','APROBADO','DESAPROBADO')",
            name="estado_seminario_valido",
        ),
        CheckConstraint("nota_final IS NULL OR (nota_final >= 1 AND nota_final <= 10)", name="nota_valida"),
        CheckConstraint("asistencias >= 0 AND total_clases >= 0", name="asistencias_validas"),
        UniqueConstraint("legajo_id", "seminario_id", name="uq_inscripcion_seminario"),
        Index("idx_inscripcion_seminario_legajo", "legajo_id"),
    )
