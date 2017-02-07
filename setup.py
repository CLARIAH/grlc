#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from distutils.core import setup
import os

with open('requirements.txt') as f:
    required = f.read().splitlines()

grlc_base = 'src/'
grlc_data = [ root.replace(grlc_base, '') + '/*' for root,dirs,files in os.walk(grlc_base) ]
grlc_version = '1.0'

setup(name='grlc',
      version=grlc_version,
      description='grlc, the git repository linked data API constructor',
      author='Albert Meroño',
      author_email='albert.merono@vu.nl',
      url='https://github.com/CLARIAH/grlc',
      download_url='https://github.com/CLARIAH/grlc/tarball/' + grlc_version,
      packages=['grlc'],
      package_dir = {'grlc': 'src'},
      package_data = {'grlc': grlc_data},
      scripts=['bin/grlc-server'],
      install_requires=required
     )
