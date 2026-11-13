"""Crea las tablas iniciales del Módulo Core.

Tablas: cohortes, legajos, documentos y auditoria_legajos (ARQUITECTURA.md §8.1).

Revision ID: 0001
Revises: 
Create Date: 2026-11-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic)
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea las tablas, restricciones e índices."""
    op.create_table('cohortes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('anio', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=50), nullable=False),
    sa.Column('abierta', sa.Boolean(), nullable=False),
    sa.Column('fecha_inicio', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('legajos',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('numero_legajo', sa.String(length=20), nullable=False),
    sa.Column('cohorte_id', sa.UUID(), nullable=False),
    sa.Column('dni', sa.String(length=20), nullable=False),
    sa.Column('apellido', sa.String(length=100), nullable=False),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('tipo_carrera', sa.String(length=30), nullable=False),
    sa.Column('solicita_beca', sa.Boolean(), nullable=False),
    sa.Column('tipo_beca', sa.String(length=10), nullable=True),
    sa.Column('estado', sa.String(length=30), nullable=False),
    sa.Column('fecha_inscripcion', sa.DateTime(), nullable=True),
    sa.Column('fecha_activacion', sa.DateTime(), nullable=True),
    sa.Column('semaforo', sa.String(length=10), nullable=False),
    sa.Column('semaforo_manual', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("estado IN ('BORRADOR','PENDIENTE','EN_REVISION','OBSERVADO','COMPLETADO','ACTIVO','VENCIDO','RECHAZADO','BAJA','GRADUADO')", name='estado_legajo_valido'),
    sa.CheckConstraint("semaforo IN ('VERDE','AMARILLO','ROJO')", name='semaforo_valido'),
    sa.CheckConstraint("tipo_carrera IN ('Especializacion','Maestria','Doctorado')", name='tipo_carrera_valido'),
    sa.ForeignKeyConstraint(['cohorte_id'], ['cohortes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('numero_legajo')
    )
    op.create_index('idx_legajos_cohorte_est', 'legajos', ['cohorte_id', 'estado'], unique=False)
    op.create_index('idx_legajos_dni', 'legajos', ['dni'], unique=False)
    op.create_index('idx_legajos_email', 'legajos', ['email'], unique=False)
    op.create_index('idx_legajos_semaforo_rojo', 'legajos', ['semaforo'], unique=False, postgresql_where="(semaforo = 'ROJO')")
    op.create_table('auditoria_legajos',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('legajo_id', sa.UUID(), nullable=False),
    sa.Column('estado_anterior', sa.String(length=30), nullable=True),
    sa.Column('estado_nuevo', sa.String(length=30), nullable=False),
    sa.Column('comentario', sa.Text(), nullable=True),
    sa.Column('usuario_email', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['legajo_id'], ['legajos.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('documentos',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('legajo_id', sa.UUID(), nullable=False),
    sa.Column('tipo', sa.String(length=50), nullable=False),
    sa.Column('path_storage', sa.String(length=500), nullable=False),
    sa.Column('nombre_original', sa.String(length=255), nullable=False),
    sa.Column('checksum_sha256', sa.String(length=64), nullable=False),
    sa.Column('tamanio_bytes', sa.Integer(), nullable=True),
    sa.Column('fecha_subida', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['legajo_id'], ['legajos.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_docs_legajo', 'documentos', ['legajo_id'], unique=False)


def downgrade() -> None:
    """Elimina todo lo creado en upgrade(), en orden inverso."""
    op.drop_index('idx_docs_legajo', table_name='documentos')
    op.drop_table('documentos')
    op.drop_table('auditoria_legajos')
    op.drop_index('idx_legajos_semaforo_rojo', table_name='legajos', postgresql_where="(semaforo = 'ROJO')")
    op.drop_index('idx_legajos_email', table_name='legajos')
    op.drop_index('idx_legajos_dni', table_name='legajos')
    op.drop_index('idx_legajos_cohorte_est', table_name='legajos')
    op.drop_table('legajos')
    op.drop_table('cohortes')