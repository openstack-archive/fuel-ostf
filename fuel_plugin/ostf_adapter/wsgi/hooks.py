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
from sqlalchemy import create_engine, orm

from pecan import hooks


LOG = logging.getLogger(__name__)


class ExceptionHandling(hooks.PecanHook):
    def on_error(self, state, e):
        LOG.exception('Pecan state %r', state)


class SessionHook(hooks.PecanHook):

    def __init__(self, dbpath):
        self.engine = create_engine(dbpath)

    def before(self, state):
        self.connection = self.engine.connect()
        state.request.session = orm.Session(bind=self.connection)

    def after(self, state):
        try:
            state.request.session.commit()
        except Exception:
            state.request.session.rollback()
            raise
        finally:
            state.request.session.close()
            self.connection.close()

    def on_error(self, state, e):
        LOG.exception('Pecan state %r', state)

        state.session.rollback()
        state.session.close()
        self.connection.close()
