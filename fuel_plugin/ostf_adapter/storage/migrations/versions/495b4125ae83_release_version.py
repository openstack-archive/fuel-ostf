"""release_version

Revision ID: 495b4125ae83
Revises: 54904076d82d
Create Date: 2015-01-22 17:24:12.963260

"""

# revision identifiers, used by Alembic.
revision = '495b4125ae83'
down_revision = '54904076d82d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('test_sets', sa.Column('release_version', sa.String(64)))
    op.add_column('tests', sa.Column('release_version', sa.String(64)))
    op.add_column('cluster_state', sa.Column('release_version', sa.String(64)))


def downgrade():
    op.drop_column('test_sets', 'release_version')
    op.drop_column('tests', 'release_version')
    op.drop_column('cluster_state', 'release_version')
