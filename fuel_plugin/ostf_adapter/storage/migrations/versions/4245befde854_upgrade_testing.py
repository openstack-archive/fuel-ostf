"""empty message

Revision ID: 4245befde854
Revises: 54904076d82d
Create Date: 2014-06-18 16:18:09.615848

"""

# revision identifiers, used by Alembic.
revision = '4245befde854'
down_revision = '54904076d82d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('test_sets', sa.Column('fuel_upgrades',
                                         sa.String(length=64), nullable=True))


def downgrade():
    op.drop_column('test_sets', 'fuel_upgrades')
