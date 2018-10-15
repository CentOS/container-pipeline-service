# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "ccp_server"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="APIs CentOS Community Container Pipeline Service",
    author_email="centos-devel@redhat.com",
    url="https://wiki.centos.org/ContainerPipeline",
    keywords=["cccp", "APIs CentOS Community Container Pipeline Service", "centos", "container"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['ccp_server=ccp_server.__main__:main']},
    long_description="""\
    This document serves as API sepcification design document for CentOS Contianer Pipeline service. Purpose of APIs- Serve the project and build information - viz [names, status, logs, etc]. Consumer of APIs -  Registry UI https://registry.centos.org, This will use the APIs to show build information - viz [build names, logs, Dockerfile, etc].
    """
)

