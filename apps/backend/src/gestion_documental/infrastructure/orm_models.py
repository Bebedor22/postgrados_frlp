"""Modelo SQLAlchemy de los documentos del legajo.

La tabla `legajos` vive en el módulo de inscripción: acá solo se la referencia por FK
(si se borra un legajo, la base borra sus documentos con ON DELETE CASCADE).
"""
import uuid
from datetime import datetime

from sqlalchemy import UUID, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from src.shared.database.connection import Base

TIPOS_DOCUMENTO_SQL = "'FORM_INSCRIPCION','DNI','TITULO_GRADO','PARTIDA','CUIT_CUIL','TITULO_POSGRADO','FORM_BECA'"


class DocumentoModel(Base):
    __tablename__ = "documentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legajo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("legajos.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo = Column(String(50), nullable=False)
    path_storage = Column(String(500), nullable=False)  # Ruta interna: nunca se expone en la API
    nombre_original = Column(String(255), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    tamanio_bytes = Column(Integer, nullable=True)
    fecha_subida = Column(DateTime, default=datetime.now)

    __table_args__ = (
        CheckConstraint(f"tipo IN ({TIPOS_DOCUMENTO_SQL})", name="tipo_doc_valido"),
        # Un documento de cada tipo por legajo: subir otro lo reemplaza
        UniqueConstraint("legajo_id", "tipo", name="uq_documento_legajo_tipo"),
        Index("idx_docs_legajo", "legajo_id"),
    )

    def __repr__(self) -> str:
        return f"<Documento {self.tipo} del legajo {self.legajo_id}>"