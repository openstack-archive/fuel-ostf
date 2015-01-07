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

"""initial

Revision ID: 53af7c2d9ccc
Revises: None
Create Date: 2013-12-04 13:32:29.109891

"""

# revision identifiers, used by Alembic.
revision = '53af7c2d9ccc'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from fuel_plugin.ostf_adapter.storage import fields


def upgrade():
    op.create_table(
        'cluster_state',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('deployment_tags', postgresql.ARRAY(sa.String(length=64)),
                  nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'test_sets',
        sa.Column('id', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('test_path', sa.String(length=256), nullable=True),
        sa.Column('driver', sa.String(length=128), nullable=True),
        sa.Column('additional_arguments', fields.ListField(), nullable=True),
        sa.Column('cleanup_path', sa.String(length=128), nullable=True),
        sa.Column('meta', fields.JsonField(), nullable=True),
        sa.Column('deployment_tags', postgresql.ARRAY(sa.String(length=64)),
                  nullable=True),
        sa.Column('test_runs_ordering_priority', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'cluster_testing_pattern',
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('test_set_id', sa.String(length=128), nullable=False),
        sa.Column('tests', postgresql.ARRAY(sa.String(length=512)),
                  nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['cluster_state.id'], ),
        sa.ForeignKeyConstraint(['test_set_id'], ['test_sets.id'], ),
        sa.PrimaryKeyConstraint('cluster_id', 'test_set_id')
    )
    op.create_table(
        'test_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('status',
                  sa.Enum('running', 'finished', name='test_run_states'),
                  nullable=False),
        sa.Column('meta', fields.JsonField(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('test_set_id', sa.String(length=128), nullable=True),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['test_set_id', 'cluster_id'],
                                ['cluster_testing_pattern.test_set_id',
                                 'cluster_testing_pattern.cluster_id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'tests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=512), nullable=True),
        sa.Column('title', sa.String(length=512), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration', sa.String(length=512), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('wait_running', 'running', 'failure',
                                    'success', 'error', 'stopped',
                                    'disabled', 'skipped', name='test_states'),
                  nullable=True),
        sa.Column('step', sa.Integer(), nullable=True),
        sa.Column('time_taken', sa.Float(), nullable=True),
        sa.Column('meta', fields.JsonField(), nullable=True),
        sa.Column('deployment_tags', postgresql.ARRAY(sa.String(length=64)),
                  nullable=True),
        sa.Column('test_run_id', sa.Integer(), nullable=True),
        sa.Column('test_set_id', sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(['test_run_id'], ['test_runs.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_set_id'], ['test_sets.id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('tests')
    op.drop_table('test_runs')
    op.drop_table('cluster_testing_pattern')
    op.drop_table('test_sets')
    op.drop_table('cluster_state')
