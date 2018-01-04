#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

# with open('README.rst') as readme_file:
#     readme = readme_file.read()
#
# with open('HISTORY.rst') as history_file:
#     history = history_file.read()

requirements = [
    # TODO: put package requirements here
]

setup_requirements = [
    # TODO(kimaero): put setup requirements (distutils extensions, etc.) here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='client_bank_exchange_1c',
    version='0.1.8',
    description="Handling of 1CClientBankExchange format",
    # long_description=readme + '\n\n' + history,
    author="Denis Kim",
    author_email='denis@kim.aero',
    url='https://git.kim.aero/taxist.info/client_bank_exchange_1c',
    packages=find_packages(include=['client_bank_exchange_1c']),
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='client_bank_exchange_1c',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Natural Language :: Russian',
        'Programming Language :: Python :: 3.6.4',
    ],
    # test_suite='tests',
    # tests_require=test_requirements,
    # setup_requires=setup_requirements,
)
