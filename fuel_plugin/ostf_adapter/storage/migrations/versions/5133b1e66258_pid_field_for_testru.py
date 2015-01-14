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

"""pid_field_for_testrun

Revision ID: 5133b1e66258
Revises: 53af7c2d9ccc
Create Date: 2014-02-14 16:34:18.751738

"""

# revision identifiers, used by Alembic.
revision = '5133b1e66258'
down_revision = '53af7c2d9ccc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('test_runs', sa.Column('pid', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('test_runs', 'pid')
