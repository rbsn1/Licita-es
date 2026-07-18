"""adiciona access_token ao cliente

Revision ID: 26a71292c50c
Revises: eaa09caf4a2e
Create Date: 2026-07-18 09:06:47.214220

"""
import secrets
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import column, table

# revision identifiers, used by Alembic.
revision: str = '26a71292c50c'
down_revision: Union[str, None] = 'eaa09caf4a2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clientes', sa.Column('access_token', sa.String(length=64), nullable=True))

    conn = op.get_bind()
    clientes_tbl = table('clientes', column('id', sa.Integer), column('access_token', sa.String))
    for row in conn.execute(sa.text('SELECT id FROM clientes')):
        conn.execute(
            clientes_tbl.update()
            .where(clientes_tbl.c.id == row.id)
            .values(access_token=secrets.token_urlsafe(32))
        )

    op.alter_column('clientes', 'access_token', nullable=False)
    op.create_unique_constraint(None, 'clientes', ['access_token'])


def downgrade() -> None:
    op.drop_constraint(None, 'clientes', type_='unique')
    op.drop_column('clientes', 'access_token')
