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

from sqlalchemy.ext.declarative import declarative_base

from adapter_utils.storage.engine import get_session, get_engine
from fuel_plugin.ostf_adapter.storage import models


def clean_up_db(db_path):
    Base = declarative_base()
    Base.metadata.reflect(bind=get_engine(db_path))

    session = get_session(db_path)
    with session.begin(subtransactions=True):
        session.query(models.TestSet).delete()
        session.query(models.ClusterState).delete()
