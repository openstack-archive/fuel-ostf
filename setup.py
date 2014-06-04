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

import setuptools


def requirements():
    return []

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

    install_requires=requirements(),

    entry_points={
        'plugins': [
            ('nose = fuel_plugin.ostf_adapter.'
             'nose_plugin.nose_adapter:NoseDriver')
        ],
        'console_scripts': [
            'ostf-server = fuel_plugin.ostf_adapter.server:main',
            ('update-commands = fuel_plugin.tests.'
             'test_utils.update_commands:main'),
            'ostfctl = adapter_utils.bin.ostf_utils:main'
        ]
    },

)
