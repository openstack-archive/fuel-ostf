from fabric.api import local


def createrole(user='ostf', password='ostf'):
    local(('psql -U postgres -c "CREATE ROLE {0} WITH PASSWORD'
        '\'{1}\' SUPERUSER CREATEDB LOGIN;"').format(user, password))


def createdb(user='ostf', database='ostf'):
    local('psql -U postgres -c "CREATE DATABASE {0} WITH OWNER={1};"'.format(database, user))


def dropdb(database='ostf'):
    local('psql -U postgres -c "DROP DATABASE {0};"'.format(database))


def deps():
    local('python setup.py egg_info && pip install -r *.egg-info/requires.txt')


def devlink():
    local('python setup.py develop')


def start_server():
    local(('ostf-server '
        '--dbpath postgresql+psycopg2://ostf:ostf@localhost/ostf'
        '--debug --debug_tests=fuel_plugin/tests/functional/dummy_tests').format(path))


def migrate():
    path='postgresql+psycopg2://ostf:ostf@localhost/ostf'
    local('ostf-server --after-initialization-environment-hook --dbpath {0}'.format(path))


def auth(method='trust'):
    """By default postgres doesnot allow auth withour password
    development without password is more fun
    """
    path = '/etc/postgresql/9.1/main/pg_hba.conf'
    wrong = '^local.*all.*postgres.*'
    right = 'local all postgres {0}'.format(method)
    local("sudo sed -i 's/{0}/{1}/' {2}".format(wrong, right, path))
    local("sudo service postgresql restart")


def remakedb():
    dropdb()
    createdb()
    migrate()