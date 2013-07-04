import multiprocessing
import setuptools


def load_requirements(requirements_path):
    with open(requirements_path, 'r') as reqs:
        return reqs.read()


setuptools.setup(

    name='ostf_tests',
    version='0.1',

    description='cloud computing testing',

    zip_safe = False,

    packages=setuptools.find_packages(),

    include_package_data=True,

    install_requires=load_requirements('pip-requires'),

)
