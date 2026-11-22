"""Módulo C: trabajos finales y fecha de último cambio de semáforo.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic)
revision: str = '0007'
down_revision: Union[str, Sequence[str], None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica la migración."""
    op.add_column('legajos', sa.Column('semaforo_desde', sa.DateTime(), nullable=True))

    op.create_table(
        'trabajos_finales',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('legajo_id', sa.UUID(), nullable=False),
        sa.Column('tipo', sa.String(length=10), nullable=False),
        sa.Column('titulo', sa.String(length=300), nullable=False),
        sa.Column('director_nombre', sa.String(length=150), nullable=False),
        sa.Column('director_email', sa.String(length=255), nullable=False),
        sa.Column('codirector_nombre', sa.String(length=150), nullable=True),
        sa.Column('fecha_aprobacion_cpr', sa.Date(), nullable=True),
        sa.Column('numero_resolucion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("tipo IN ('TFI','TESIS')", name='tipo_trabajo_final_valido'),
        sa.ForeignKeyConstraint(
            ['legajo_id'], ['legajos.id'], ondelete='CASCADE', name='fk_trabajos_finales_legajo'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('legajo_id', name='uq_trabajo_final_por_legajo'),
    )


def downgrade() -> None:
    """Revierte la migración."""
    op.drop_table('trabajos_finales')
    op.drop_column('legajos', 'semaforo_desde')
