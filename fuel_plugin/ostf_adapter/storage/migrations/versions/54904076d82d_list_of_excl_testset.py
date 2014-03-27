"""list_of_excl_testsets

Revision ID: 54904076d82d
Revises: 53af7c2d9ccc
Create Date: 2014-02-13 18:57:46.854934

"""

# revision identifiers, used by Alembic.
revision = '54904076d82d'
down_revision = '5133b1e66258'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.add_column('test_sets', sa.Column('exclusive_testsets',
                                         postgresql.ARRAY(
                                             sa.String(length=128)
                                         ),
                                         nullable=True))


def downgrade():
    op.drop_column('test_sets', 'exclusive_testsets')
