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


class CustomTransactionalHook(hooks.TransactionHook):
    def __init__(self, dbpath):
        engine = create_engine(dbpath)
        self.session = orm.scoped_session(orm.sessionmaker())
        self.session.configure(bind=engine)

        def start():
            pass

        def commit():
            self.session.commit()

        def rollback():
            self.session.rollback()

        def clear():
            # not all GET controllers doesn't write to db
            self.session.commit()

            self.session.remove()

        super(CustomTransactionalHook, self).__init__(start,
                                                      start,
                                                      commit,
                                                      rollback,
                                                      clear)

    def before(self, state):
        super(CustomTransactionalHook, self).before(state)
        state.request.session = self.session

    def on_error(self, state, exc):
        super(CustomTransactionalHook, self).on_error(state, exc)
        LOG.exception('Pecan state %r', state)


class AddTokenHook(hooks.PecanHook):

    def before(self, state):
        # (dshulyak) just utility to get token
        state.request.token = state.request.headers.get('X-Auth-Token', None)
