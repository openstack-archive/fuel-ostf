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
           '--nailgun-port=8888 '
           '--debug_tests=fuel_plugin/tests/functional/dummy_tests'))


def startnailgunmimic():
    path = 'fuel_plugin/tests/test_utils/nailgun_mimic.py'
    local('python {0}'.format(path))


def createmigration(comment):
    '''
    Supply comment for new alembic revision as a value
    for comment argument
    '''
    config_path = 'fuel_plugin/ostf_adapter/storage/alembic.ini'
    local(
        'alembic --config {0} revision --autogenerate -m \"{1}\"'
        .format(config_path, comment)
    )


def migrate(database='ostf'):
    path = 'postgresql+psycopg2://ostf:ostf@localhost/{0}'.format(database)
    local('ostf-server --after-initialization-environment-hook --dbpath {0}'.format(path))


def auth(method='trust', os='ubuntu'):
    """By default postgres doesnot allow auth withour password
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
    local('nosetests fuel_plugin/tests/functional/tests.py:AdapterTests -v')


def unit():
    local('nosetests fuel_plugin/tests/unit -v')
