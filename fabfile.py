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

from fabric.api import local


def createrole(user='ostf', password='ostf'):
    local(('psql -U postgres -c "CREATE ROLE {0} WITH PASSWORD'
           '\'{1}\' SUPERUSER CREATEDB LOGIN;"').format(user, password))


def createdb(user='ostf', database='ostf'):
    local(
        'psql -U postgres -c "CREATE DATABASE {0} WITH OWNER={1};"'
        .format(database, user)
    )


def dropdb(database='ostf'):
    local('psql -U postgres -c "DROP DATABASE {0};"'.format(database))


def deps():
    local('python setup.py egg_info && pip install -r *.egg-info/requires.txt')


def devlink():
    local('python setup.py develop')


def testdeps():
    local('pip install -r test-requires')


def startserver():
    local(('ostf-server '
           '--dbpath postgresql+psycopg2://ostf:ostf@localhost/ostf '))


def startdebugserver():
    local(('ostf-server '
           '--debug '
           '--debug_tests=fuel_plugin/testing/fixture/dummy_tests'))


def startnailgunmimic():
    path = 'fuel_plugin/testing/test_utils/nailgun_mimic.py'
    local('python {0}'.format(path))


def createmigration(comment):
    '''Supply comment for new alembic revision as a value
    for comment argument
    '''
    config_path = 'fuel_plugin/ostf_adapter/storage/alembic.ini'
    local(
        'alembic --config {0} revision --autogenerate -m \"{1}\"'
        .format(config_path, comment)
    )


def migrate(database='ostf'):
    local(
        'ostf-server --after-initialization-environment-hook'
    )


def auth(method='trust', os='ubuntu'):
    """By default postgres doesn't allow auth without password
    development without password is more fun
    """
    if os == 'centos':
        path = '/var/lib/pgsql/data/pg_hba.conf'
    elif os == 'ubuntu':
        path = '/etc/postgresql/9.1/main/pg_hba.conf'

    wrong = '^local.*all.*postgres.*'
    right = 'local all postgres {0}'.format(method)
    local("sudo sed -i 's/{0}/{1}/' {2}".format(wrong, right, path))
    local("sudo service postgresql restart")


def remakedb(database='ostf'):
    dropdb(database=database)
    createdb(database=database)
    migrate(database=database)


def installapp():
    deps()
    devlink()
    testdeps()


def testall():
    unit()
    integration()


def integration():
    local(
        ('nosetests fuel_plugin/testing/'
         'tests/functional/tests.py:AdapterTests -vs')
    )


def unit():
    local('nosetests fuel_plugin/testing/tests/unit -v')
