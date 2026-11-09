"""Modelos SQLAlchemy del módulo de inscripción.

Solo en la capa de infraestructura vive SQLAlchemy. Todos los modelos usan la
misma `Base` declarada en `src/shared/database/connection.py`, así Alembic y
`crear_todas_las_tablas()` ven todas las tablas.
La tabla \cohortes` está en `src/oferta_academica/infrastructure/orm_models.py`.`
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.shared.database.connection import Base

class LegajoModel(Base):
    __tablename__ = "legajos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_legajo = Column(String(20), unique=True, nullable=False)
    cohorte_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cohortes.id", ondelete="CASCADE"),
        nullable=False,
    )
    dni = Column(String(20), nullable=False)
    apellido = Column(String(100), nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    tipo_carrera = Column(String(30), nullable=False)
    solicita_beca = Column(Boolean, nullable=False, default=False)
    tipo_beca = Column(String(10))
    estado = Column(String(30), nullable=False, default="BORRADOR")
    fecha_inscripcion = Column(DateTime, nullable=True)
    fecha_activacion = Column(DateTime, nullable=True)
    semaforo = Column(String(10), nullable=False, default="VERDE")
    semaforo_manual = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relaciones (la cohorte vive en el módulo oferta_academica: solo se referencia por FK)
    documentos = relationship("DocumentoModel", back_populates="legajo", cascade="all, delete-orphan")
    auditoria = relationship("AuditoriaLegajoModel", back_populates="legajo", cascade="all, delete-orphan")

    __table_args__ = (
        # Reglas de integridad del modelo de datos (ARQUITECTURA.md §8.1)
        CheckConstraint(
            "estado IN ('BORRADOR','PENDIENTE','EN_REVISION','OBSERVADO','COMPLETADO',"
            "'ACTIVO','VENCIDO','RECHAZADO','BAJA','GRADUADO')",
            name="estado_legajo_valido",
        ),
        CheckConstraint(
            "tipo_carrera IN ('Especializacion','Maestria','Doctorado')",
            name="tipo_carrera_valido",
        ),
        CheckConstraint("semaforo IN ('VERDE','AMARILLO','ROJO')", name="semaforo_valido"),
        Index("idx_legajos_dni", "dni"),
        Index("idx_legajos_email", "email"),
        Index("idx_legajos_cohorte_est", "cohorte_id", "estado"),
        Index(
            "idx_legajos_semaforo_rojo",
            "semaforo",
            postgresql_where="(semaforo = 'ROJO')",
        ),
    )

    def __repr__(self) -> str:
        return f"<Legajo {self.numero_legajo} - {self.apellido}, {self.nombre}>"


class DocumentoModel(Base):
    __tablename__ = "documentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legajo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("legajos.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo = Column(String(50), nullable=False)
    path_storage = Column(String(500), nullable=False)  # Nunca pública, solo vía endpoint
    nombre_original = Column(String(255), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    tamanio_bytes = Column(Integer, nullable=True)
    fecha_subida = Column(DateTime, default=datetime.now)

    legajo = relationship("LegajoModel", back_populates="documentos")

    __table_args__ = (Index("idx_docs_legajo", "legajo_id"),)

    def __repr__(self) -> str:
        return f"<Documento {self.id} para legajo {self.legajo_id}>"


class AuditoriaLegajoModel(Base):
    """Historial de cambios de estado de cada legajo (quién, cuándo y por qué)."""

    __tablename__ = "auditoria_legajos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legajo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("legajos.id", ondelete="CASCADE"),
        nullable=False,
    )
    estado_anterior = Column(String(30))
    estado_nuevo = Column(String(30), nullable=False)
    comentario = Column(Text)
    usuario_email = Column(String(255))  # NULL si el cambio fue automático
    created_at = Column(DateTime, default=datetime.now)

    legajo = relationship("LegajoModel", back_populates="auditoria")