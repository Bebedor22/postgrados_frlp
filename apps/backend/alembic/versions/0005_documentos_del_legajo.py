"""Documentos del legajo (RF-CORE-002).

- Solo los tipos de documento del SRS (CHECK tipo_doc_valido).
- Un documento de cada tipo por legajo: subir otro del mismo tipo lo reemplaza.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-11

"""
from typing import Sequence, Union

from alembic import op


# Identificadores de la revisión (Alembic)
revision: str = '0005'
down_revision: Union[str, Sequence[str], None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TIPOS = "'FORM_INSCRIPCION','DNI','TITULO_GRADO','PARTIDA','CUIT_CUIL','TITULO_POSGRADO','FORM_BECA'"


def upgrade() -> None:
    """Aplica la migración."""
    op.create_check_constraint('tipo_doc_valido', 'documentos', f"tipo IN ({TIPOS})")
    op.create_unique_constraint('uq_documento_legajo_tipo', 'documentos', ['legajo_id', 'tipo'])


def downgrade() -> None:
    """Revierte la migración."""
    op.drop_constraint('uq_documento_legajo_tipo', 'documentos', type_='unique')
    op.drop_constraint('tipo_doc_valido', 'documentos', type_='check')