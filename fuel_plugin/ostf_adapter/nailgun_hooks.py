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

from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from sqlalchemy import MetaData
from sqlalchemy import schema

from fuel_plugin.ostf_adapter.storage import alembic_cli

LOG = logging.getLogger(__name__)


def clear_db(dbpath):
    """Clean database (to prevent issue with changed
    head revision script) and upgrade to head revision.

    Expect 0 on success by nailgun
    Exception is good enough signal that something goes wrong
    """
    db_engine = create_engine(dbpath)
    conn = db_engine.connect()
    trans = conn.begin()
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
                schema.ForeignKeyConstraint((), (), name=fk['name'])
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

    custom_types = conn.execute(
        "SELECT n.nspname as schema, t.typname as type "
        "FROM pg_type t LEFT JOIN pg_catalog.pg_namespace n "
        "ON n.oid = t.typnamespace "
        "WHERE (t.typrelid = 0 OR (SELECT c.relkind = 'c' "
        "FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid)) "
        "AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el "
        "WHERE el.oid = t.typelem AND el.typarray = t.oid) "
        "AND     n.nspname NOT IN ('pg_catalog', 'information_schema')"
    )

    for tp in custom_types:
        conn.execute("DROP TYPE {0}".format(tp[1]))
    trans.commit()
    alembic_cli.drop_migration_meta(db_engine)
    conn.close()
    db_engine.dispose()
    return 0


def after_initialization_environment_hook():
    """Expect 0 on success by nailgun
    Exception is good enough signal that something goes wrong
    """
    alembic_cli.do_apply_migrations()
    return 0
