#!/usr/bin/env python

import os
import fnmatch
import subprocess

## prepare to run PyTest as a command
from distutils.core import Command

from setuptools import setup, find_packages

from version import get_git_version
VERSION, SOURCE_LABEL = get_git_version()
PROJECT = 'trec_dd'
URL = 'http://trec-dd.org/'
AUTHOR = 'Diffeo, Inc.'
AUTHOR_EMAIL = 'support@diffeo.com'
DESC = 'TREC Dynamic Domain (DD) evaluation test harness for simulating user interaction with a search engine'


def read_file(file_name):
    file_path = os.path.join(
        os.path.dirname(__file__),
        file_name
        )
    return open(file_path).read()


def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results


def recursive_glob_with_tree(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        one_dir_results = []
        for f in goodfiles:
            one_dir_results.append(os.path.join(base, f))
        results.append((base, one_dir_results))
    return results


def _myinstall(pkgspec):
    subprocess.check_call(['pip', 'install', pkgspec])


class PyTest(Command):
    '''run py.test'''

    description = 'runs py.test to execute all tests'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if self.distribution.install_requires:
            for ir in self.distribution.install_requires:
                _myinstall(ir)
        if self.distribution.tests_require:
            for ir in self.distribution.tests_require:
                _myinstall(ir)

        errno = subprocess.call(['py.test', '-n', '3', '-s', 'trec_dd', '--runslow', '--runperf'])
        raise SystemExit(errno)

setup(
    name=PROJECT,
    version=VERSION,
    description=DESC,
    long_description=read_file('README.rst'),
    author=AUTHOR,
    license='MIT/X11 license http://opensource.org/licenses/MIT',
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages=find_packages(),
    cmdclass={
        'test': PyTest,
    },
    # We can select proper classifiers later
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',  ## MIT/X11 license http://opensource.org/licenses/MIT
    ],
    install_requires=[
        'dossier.label',
        'lxml',
        'beautifulsoup4',
    ],
    extras_require={
        'postgres': [
            'psycopg2',
        ],
        'mysql': [
            'kvlayer_mysql',
        ],
    },        
    entry_points={
        'console_scripts': [
            'trec_dd_harness = trec_dd.harness.run:main',
            'trec_dd_scorer = trec_dd.scorer.run:main',
            'trec_dd_random_system = trec_dd.system.random_system:main',
        ]
    },
    scripts=['bin/cubeTest.pl'],
    include_package_data=True,
)
