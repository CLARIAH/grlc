#!/usr/bin/env python

from distutils.core import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='grlc',
      version='1.0',
      description='grlc, the git repository linked data API constructor',
      author='Albert Meroño',
      url='https://github.com/CLARIAH/grlc',
      packages=['grlc'],
      package_dir = {'grlc': 'src'},
      scripts=['bin/grlc-server'],
      install_requires=required
     )
