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

from distutils import version
import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from sqlalchemy import inspect
from sqlalchemy import MetaData
from sqlalchemy.pool import NullPool
from sqlalchemy import schema

from fuel_plugin.ostf_adapter.storage import alembic_cli

LOG = logging.getLogger(__name__)


def _get_enums(conn):
    """Return names for db types.
    Please, be awared that for sqlalchemy of version >= 1.0.0
    get_enums() method of inspection object is available for the
    purpose.

    Also this approach will work only for postgresql dialect.
    """
    from sqlalchemy import __version__
    if version.StrictVersion(__version__) >= version.StrictVersion("1.0.0"):
        return [e['name'] for e in inspect(conn).get_enums()]
    else:
        return conn.dialect._load_enums(conn).keys()


def clear_db(db_path):
    db_engine = create_engine(db_path, poolclass=NullPool)
    with db_engine.begin() as conn:
        meta = MetaData()
        meta.reflect(bind=db_engine)
        inspector = reflection.Inspector.from_engine(db_engine)

        tbs = []
        all_fks = []

        for table_name in inspector.get_table_names():
            fks = []
            for fk in inspector.get_foreign_keys(table_name):
                if not fk['name']:
                    continue
                fks.append(
                    schema.ForeignKeyConstraint(tuple(),
                                                tuple(),
                                                name=fk['name'])
                )
            t = schema.Table(
                table_name,
                meta,
                *fks,
                extend_existing=True
            )
            tbs.append(t)
            all_fks.extend(fks)

        for fkc in all_fks:
            conn.execute(schema.DropConstraint(fkc))

        for table in tbs:
            conn.execute(schema.DropTable(table))

        for en in _get_enums(conn):
            conn.execute("DROP TYPE {0}".format(en))

        alembic_cli.drop_migration_meta(conn)


def after_initialization_environment_hook():
    """Expect 0 on success by nailgun
    Exception is good enough signal that something goes wrong
    """
    alembic_cli.do_apply_migrations()
    return 0
