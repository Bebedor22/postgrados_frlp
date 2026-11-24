"""Crea la tabla de carreras.

Catálogo de carreras de posgrado (gestionado por la Dirección y la conducción).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic)
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica la migración."""
    op.create_table('carreras',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('nombre', sa.String(length=150), nullable=False),
    sa.Column('tipo', sa.String(length=30), nullable=False),
    sa.Column('duracion_anios', sa.Integer(), nullable=False),
    sa.Column('activa', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("tipo IN ('Especializacion','Maestria','Doctorado')", name='tipo_carrera_valido'),
    sa.CheckConstraint('duracion_anios BETWEEN 1 AND 6', name='duracion_valida'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )


def downgrade() -> None:
    """Revierte la migración."""
    op.drop_table('carreras')