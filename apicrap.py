#!/usr/bin/env python

import urllib2
import json
import sys

stream = urllib2.urlopen(sys.argv[1])
resp = json.load(stream)

for c in resp:
    print c["name"]
    print c["download_url"]

exit(0)


