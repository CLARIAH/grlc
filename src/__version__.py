# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

import os
import sys
import yaml

# To update the package version number, edit CITATION.cff
citationfile = os.path.join(sys.exec_prefix, 'citation/grlc', 'CITATION.cff')
with open(citationfile, 'r') as f:
    data = yaml.safe_load(f)
    __version__ = data['version']
