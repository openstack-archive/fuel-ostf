#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""versioning

Revision ID: 36e3fd684a9e
Revises: 54904076d82d
Create Date: 2015-02-12 15:45:23.885397

"""

# revision identifiers, used by Alembic.
revision = '36e3fd684a9e'
down_revision = '54904076d82d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('test_sets', sa.Column('available_since_release',
                                         sa.String(64),
                                         default=""))
    op.add_column('tests', sa.Column('available_since_release',
                                     sa.String(64),
                                     default=""))
    op.add_column('cluster_state', sa.Column('release_version', sa.String(64)))


def downgrade():
    op.drop_column('test_sets', 'available_since_release')
    op.drop_column('tests', 'available_since_release')
    op.drop_column('cluster_state', 'release_version')
