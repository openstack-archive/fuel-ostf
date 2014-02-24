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

from sqlalchemy import create_engine, orm, pool


_ENGINE = None
_MAKER = None


def instantiate_db_toolkit(dbpath, session_params):
    '''Performs creation of SQLAlchemy engine and
    Sessionmaker which will be saved in global variables
    for further using.

    Params:
        1) dbpath -- connection string for create_engine function
        2) session_params -- dict with different params for settuping
        sqlaclhemy session.
    '''
    global _ENGINE
    global _MAKER

    _ENGINE = create_engine(dbpath, poolclass=pool.NullPool)
    _MAKER = orm.sessionmaker(bind=_ENGINE, **session_params)


def get_session():
    """Returns a SQLAlchemy session."""
    return _MAKER()


def get_engine():
    """Returns instance of sqlalchemy engine"""
    return _ENGINE
