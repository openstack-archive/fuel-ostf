# -*- coding: utf-8 -*-

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
