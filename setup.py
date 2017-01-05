#!/usr/bin/env python

from distutils.core import setup
import os

with open('requirements.txt') as f:
    required = f.read().splitlines()

grlc_base = 'src/'
grlc_data = [ root.replace(grlc_base, '') + '/*' for root,dirs,files in os.walk(grlc_base) ]

setup(name='grlc',
      version='1.0',
      description='grlc, the git repository linked data API constructor',
      author='Albert Meroño',
      url='https://github.com/CLARIAH/grlc',
      packages=['grlc'],
      package_dir = {'grlc': 'src'},
      package_data = {'grlc': grlc_data},
      scripts=['bin/grlc-server'],
      install_requires=required
     )
