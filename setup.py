#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import codecs
import os
from setuptools import setup

grlc_base = 'src'
grlc_base_dir = os.path.join(grlc_base, '')
grlc_data = []
for root,dirs,files in os.walk(grlc_base):
    if root != grlc_base:
        root_dir = root.replace(grlc_base_dir, '')
        data_files = os.path.join(root_dir, '*')
        grlc_data.append(data_files)
grlc_version = '1.3.1'

with codecs.open('requirements.txt', mode='r') as f:
    install_requires = f.read().splitlines()

with codecs.open('requirements-test.txt', mode='r') as f:
    tests_require = f.read().splitlines()

with codecs.open('README.md', mode='r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="grlc",
    description='grlc, the git repository linked data API constructor',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="Copyright 2017 Albert Meroño",
    author='Albert Meroño',
    author_email='albert.merono@vu.nl',
    url='https://github.com/CLARIAH/grlc',
    version=grlc_version,
    py_modules=['grlc'],
    packages=['grlc'],
    package_dir = {'grlc': grlc_base},
    scripts=['bin/grlc-server'],
    install_requires=install_requires,
    setup_requires=[
        # dependency for `python setup.py test`
        'pytest-runner',
        # dependencies for `python setup.py build_sphinx`
        'sphinx',
        'recommonmark'
    ],
    tests_require=tests_require,
    package_data = {'grlc': grlc_data},
)
