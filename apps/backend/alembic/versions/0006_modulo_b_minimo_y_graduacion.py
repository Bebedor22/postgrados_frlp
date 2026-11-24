"""Módulo B mínimo y fecha de graduación del Core.

- seminarios: catálogo por carrera, con obligatoriedad y datos para recordatorios.
- inscripcion_seminario: qué cursó y aprobó cada legajo (insumo del semáforo).
- legajos.fecha_graduacion: fecha usada por las métricas del Módulo D.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic)
revision: str = '0006'
down_revision: Union[str, Sequence[str], None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica la migración."""
    op.add_column('legajos', sa.Column('fecha_graduacion', sa.DateTime(), nullable=True))

    op.create_table(
        'seminarios',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('carrera_id', sa.UUID(), nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('horas_catedra', sa.Integer(), nullable=False),
        sa.Column('es_obligatorio', sa.Boolean(), nullable=False),
        sa.Column('docente_email', sa.String(length=255), nullable=True),
        sa.Column('fecha_limite_actas', sa.Date(), nullable=True),
        sa.Column('actualizado_en', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('horas_catedra >= 0', name='horas_catedra_validas'),
        sa.ForeignKeyConstraint(['carrera_id'], ['carreras.id'], ondelete='CASCADE', name='fk_seminarios_carrera'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo'),
    )
    op.create_index('idx_seminarios_carrera', 'seminarios', ['carrera_id'], unique=False)

    op.create_table(
        'inscripcion_seminario',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('legajo_id', sa.UUID(), nullable=False),
        sa.Column('seminario_id', sa.UUID(), nullable=False),
        sa.Column('nota_final', sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column('asistencias', sa.Integer(), nullable=False),
        sa.Column('total_clases', sa.Integer(), nullable=False),
        sa.Column('estado', sa.String(length=20), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "estado IN ('CURSANDO','APROBADO','DESAPROBADO')",
            name='estado_seminario_valido',
        ),
        sa.CheckConstraint(
            'nota_final IS NULL OR (nota_final >= 1 AND nota_final <= 10)',
            name='nota_valida',
        ),
        sa.CheckConstraint('asistencias >= 0 AND total_clases >= 0', name='asistencias_validas'),
        sa.ForeignKeyConstraint(
            ['legajo_id'], ['legajos.id'], ondelete='CASCADE', name='fk_inscripcion_seminario_legajo'
        ),
        sa.ForeignKeyConstraint(
            ['seminario_id'], ['seminarios.id'], ondelete='CASCADE', name='fk_inscripcion_seminario_seminario'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('legajo_id', 'seminario_id', name='uq_inscripcion_seminario'),
    )
    op.create_index('idx_inscripcion_seminario_legajo', 'inscripcion_seminario', ['legajo_id'], unique=False)


def downgrade() -> None:
    """Revierte la migración."""
    op.drop_index('idx_inscripcion_seminario_legajo', table_name='inscripcion_seminario')
    op.drop_table('inscripcion_seminario')
    op.drop_index('idx_seminarios_carrera', table_name='seminarios')
    op.drop_table('seminarios')
    op.drop_column('legajos', 'fecha_graduacion')
