"""Crea la tabla de usuarios del sistema.

Usuarios con login (coordinador, docente, CPR, Dirección de Posgrado, admin) y su rol (ARQUITECTURA.md §7.2).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic)
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica la migración."""
    op.create_table('usuarios',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('nombre', sa.String(length=150), nullable=False),
    sa.Column('rol', sa.String(length=20), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("rol IN ('ASPIRANTE','DOCENTE','COORDINADOR','CPR','DIRECCION','ADMIN')", name='rol_valido'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)


def downgrade() -> None:
    """Revierte la migración."""
    op.drop_index(op.f('ix_usuarios_email'), table_name='usuarios')
    op.drop_table('usuarios')