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
    'pbr==0.5.17',
    'pika==0.9.13',
    'prettytable==0.7.2',
    'pyOpenSSL==0.13',
    'pycrypto==2.6',
    'pyparsing==1.5.7',
    'python-cinderclient==1.0.4',
    'python-glanceclient==0.9.0',
    'python-keystoneclient==0.3.1',
    'python-mimeparse==0.1.4',
    'python-novaclient==2.13.0',
    'python-quantumclient==2.2.3',
    'requests==1.2.3',
    'setuptools-git==1.0',
    'simplejson==3.3.0',
    'unittest2',
    'six==1.3.0',
    'testresources==0.2.7',
    'warlock==1.0.1',
    'wsgiref==0.1.2',
    'yaml==3.10'
]


setuptools.setup(

    name='ostf_tests',
    version='0.1',

    description='cloud computing testing',

    zip_safe=False,

    packages=setuptools.find_packages(),

    include_package_data=True,

    install_requires=requirements,

)
