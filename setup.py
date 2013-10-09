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


fuel_health_reqs = [
    'oslo.config>=1.1.1',
    'python-cinderclient==1.0.4',
    'python-glanceclient==0.9.0',
    'python-keystoneclient==0.2.4',
    'python-neutronclient==2.3.1',
    'python-novaclient==2.12.0',
    'python-heatclient==0.2.2',
    'python-muranoclient==0.2',
    'python-savannaclient>=0.2.2',
    'paramiko>=1.10.1',
    'requests>=1.1,<1.2.3',
    'unittest2>=0.5.1',
    'pyyaml>=3.10',
    'testresources>=0.2.7'
]

fuel_ostf_reqs = [
    'nose>=1.3.0',
    'SQLAlchemy>=0.8.2',
    'alembic>=0.5.0',
    'gevent==0.13.8',
    'pecan>=0.3.0',
    'psycopg2>=2.5.1',
    'stevedore>=0.10'
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

    name='fuel-ostf',
    version='0.1',

    description='cloud computing testing',

    zip_safe=False,

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

    include_package_data=True,

    packages=setuptools.find_packages(),

    install_requires=fuel_health_reqs+fuel_ostf_reqs,

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
