"""adiciona resumo_edital e faixa_preco

Revision ID: c1a0f5d9b2e4
Revises: 94edff7d48c9
Create Date: 2026-07-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1a0f5d9b2e4'
down_revision: Union[str, None] = '94edff7d48c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('resumos_edital',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('edital_id', sa.Integer(), nullable=False),
    sa.Column('prazo_limite_proposta', sa.DateTime(), nullable=True),
    sa.Column('valor_estimado', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('requisitos_habilitacao', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('clausulas_risco', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['edital_id'], ['editais.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('edital_id')
    )
    op.create_table('faixas_preco',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('edital_id', sa.Integer(), nullable=False),
    sa.Column('minimo', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('ideal', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('maximo', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('confiavel', sa.Boolean(), nullable=False),
    sa.Column('amostra', sa.Integer(), nullable=False),
    sa.Column('criado_em', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['edital_id'], ['editais.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('edital_id')
    )


def downgrade() -> None:
    op.drop_table('faixas_preco')
    op.drop_table('resumos_edital')
