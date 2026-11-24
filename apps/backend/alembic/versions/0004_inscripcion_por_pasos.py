"""Inscripción por pasos con "cargar y guardar".

- Tabla datos_aspirante: el formulario completo del enunciado (1 a 1 con el legajo).
- legajos: carrera elegida, tipo de documento (DNI o pasaporte) y hash del token de seguimiento.
- Se quita el email único: la misma persona puede inscribirse a 2 carreras (BR-001).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores de la revisión (Alembic)
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Aplica la migración."""
    op.create_table('datos_aspirante',
    sa.Column('legajo_id', sa.UUID(), nullable=False),
    sa.Column('nacionalidad', sa.String(length=60), nullable=True),
    sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
    sa.Column('genero', sa.String(length=30), nullable=True),
    sa.Column('email_alternativo', sa.String(length=255), nullable=True),
    sa.Column('telefono_movil', sa.String(length=30), nullable=True),
    sa.Column('telefono_fijo', sa.String(length=30), nullable=True),
    sa.Column('calle', sa.String(length=120), nullable=True),
    sa.Column('numero', sa.String(length=10), nullable=True),
    sa.Column('piso_depto', sa.String(length=20), nullable=True),
    sa.Column('codigo_postal', sa.String(length=10), nullable=True),
    sa.Column('ciudad', sa.String(length=80), nullable=True),
    sa.Column('provincia', sa.String(length=80), nullable=True),
    sa.Column('pais', sa.String(length=60), nullable=True),
    sa.Column('titulo_grado', sa.String(length=150), nullable=True),
    sa.Column('institucion_grado', sa.String(length=150), nullable=True),
    sa.Column('anio_graduacion', sa.Integer(), nullable=True),
    sa.Column('titulo_posgrado', sa.String(length=150), nullable=True),
    sa.Column('como_conocio', sa.String(length=30), nullable=True),
    sa.Column('como_conocio_detalle', sa.String(length=150), nullable=True),
    sa.Column('motivacion', sa.Text(), nullable=True),
    sa.Column('trabaja_en_area', sa.Boolean(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint("como_conocio IN ('SITIO_WEB','OTROS_SITIOS_WEB','EGRESADOS_UTN','COLEGAS','OTROS')", name='como_conocio_valido'),
    sa.ForeignKeyConstraint(['legajo_id'], ['legajos.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('legajo_id')
    )
    op.add_column('legajos', sa.Column('carrera_id', sa.UUID(), nullable=True))
    op.add_column('legajos', sa.Column('tipo_documento', sa.String(length=10), server_default='DNI', nullable=False))
    op.add_column('legajos', sa.Column('token_seguimiento_hash', sa.String(length=64), nullable=True))
    op.create_foreign_key('fk_legajos_carrera', 'legajos', 'carreras', ['carrera_id'], ['id'])
    op.create_check_constraint('tipo_documento_valido', 'legajos', "tipo_documento IN ('DNI','PASAPORTE')")
    op.drop_constraint('legajos_email_key', 'legajos', type_='unique')
    op.create_unique_constraint(
        'uq_inscripcion_documento_cohorte_carrera', 'legajos', ['dni', 'cohorte_id', 'carrera_id']
    )
    op.create_unique_constraint('uq_legajos_token_seguimiento', 'legajos', ['token_seguimiento_hash'])


def downgrade() -> None:
    """Revierte la migración."""
    op.drop_constraint('uq_legajos_token_seguimiento', 'legajos', type_='unique')
    op.drop_constraint('uq_inscripcion_documento_cohorte_carrera', 'legajos', type_='unique')
    op.create_unique_constraint('legajos_email_key', 'legajos', ['email'])
    op.drop_constraint('tipo_documento_valido', 'legajos', type_='check')
    op.drop_constraint('fk_legajos_carrera', 'legajos', type_='foreignkey')
    op.drop_column('legajos', 'token_seguimiento_hash')
    op.drop_column('legajos', 'tipo_documento')
    op.drop_column('legajos', 'carrera_id')
    op.drop_table('datos_aspirante')