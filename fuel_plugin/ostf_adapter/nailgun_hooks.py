#    Copyright 2013 Mirantis, Inc.
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

import logging
from fuel_plugin.ostf_adapter.storage import alembic_cli
from fuel_plugin.ostf_adapter.storage import engine, models

LOG = logging.getLogger(__name__)


def after_initialization_environment_hook():
    """Expect 0 on success by nailgun
    Exception is good enough signal that something goes wrong
    """
    alembic_cli.do_apply_migrations()
    return 0


def clean_up_db():
    session = engine.get_session()
    with session.begin(subtransactions=True):
        session.query(models.TestSet).delete()
        session.query(models.ClusterState).delete()
