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

#def get_session(autocommit=True, expire_on_commit=False):
#    """Return a SQLAlchemy session."""
#    global _MAKER
#    global _SLAVE_MAKER
#    maker = _MAKER
#
#    if maker is None:
#        engine = get_engine()
#        maker = get_maker(engine, autocommit, expire_on_commit)
#
#    else:
#        _MAKER = maker
#
#    session = maker()
#    return session
#
#
#def get_engine(dbpath=None, pool_type=None):
#    """Return a SQLAlchemy engine."""
#    global _ENGINE
#    engine = _ENGINE
#
#    if engine is None:
#        engine = create_engine(dbpath,
#                               poolclass=pool_type or pool.NullPool)
#    _ENGINE = engine
#    return engine
#
#
#def get_maker(engine, autocommit=True, expire_on_commit=False):
#    """Return a SQLAlchemy sessionmaker using the given engine."""
#    return orm.sessionmaker(
#        bind=engine,
#        autocommit=autocommit,
#        expire_on_commit=expire_on_commit)
