import os
import sys
import yaml

citationfile = os.path.join(sys.exec_prefix, 'citation/grlc', 'CITATION.cff')
with open(citationfile, 'r') as f:
    data = yaml.safe_load(f)
    __version__ = data['version']
