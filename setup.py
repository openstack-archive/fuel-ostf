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

import multiprocessing
import setuptools


requirements = [
    'argparse==1.2.1',
    'cliff==1.4',
    'cmd2==0.6.5.1',
    'd2to1==0.2.10',
    'distribute==0.7.3',
    'extras==0.0.3',
    'httplib2==0.8',
    'iso8601==0.1.4',
    'jsonpatch==1.1',
    'jsonpointer==1.0',
    'jsonschema==2.0.0',
    'netaddr==0.7.10',
    'nose==1.3.0',
    'oslo.config==1.1.1',
    'paramiko==1.10.1',
    'prettytable==0.7.2',
    'pyOpenSSL==0.13',
    'pycrypto==2.6',
    'pyparsing==1.5.7',
    'python-cinderclient==1.0.4',
    'python-glanceclient==0.9.0',
    'python-keystoneclient==0.3.1',
    'python-mimeparse==0.1.4',
    'python-novaclient==2.13.0',
    'requests==1.2.3',
    'setuptools-git==1.0',
    'simplejson==3.3.0',
    'unittest2',
    'six==1.3.0',
    'testresources==0.2.7',
    'warlock==1.0.1',
    'wsgiref==0.1.2',
    'pyyaml==3.10',
    'Mako==0.8.1',
    'MarkupSafe==0.18',
    'SQLAlchemy==0.8.2',
    'WebOb==1.2.3',
    'WebTest==2.0.6',
    'alembic==0.5.0',
    'beautifulsoup4==4.2.1',
    'gevent==0.13.8',
    'greenlet==0.4.1',
    'pecan==0.3.0',
    'psycogreen==1.0',
    'psycopg2==2.5.1',
    'simplegeneric==0.8.1',
    'stevedore==0.10',
    'waitress==0.8.5',
    'WSME==0.5b2'
]

test_requires = [
    'mock==1.0.1',
    'pep8==1.4.6',
    'py==1.4.15',
    'six==1.3.0',
    'tox==1.5.0',
    'unittest2',
    'nose',
    'requests'
]


setuptools.setup(

    name='fuel_ostf',
    version='0.1',

    description='cloud computing testing',

    zip_safe=False,

    test_suite='fuel_plugin/tests',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Setuptools Plugin',
        'Environment :: OpenStack',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Testing',
    ],

    packages=setuptools.find_packages(),

    include_package_data=True,

    install_requires=requirements,

    entry_points={
        'plugins': [
            ('nose = fuel_plugin.ostf_adapter.'
             'nose_plugin.nose_adapter:NoseDriver')
        ],
        'console_scripts': [
            'ostf-server = fuel_plugin.bin.adapter_api:main',
            ('update-commands = fuel_plugin.tests.'
             'test_utils.update_commands:main')
        ]
    },

)
