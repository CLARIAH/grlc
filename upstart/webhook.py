#!/usr/bin/env python

from flask import Flask
from subprocess import call
import os
app = Flask(__name__)

@app.route("/", method=['POST'])
def update():
    print "Starting image update"
    call(['docker', 'pull', 'clariah/grlc:dev'])
    os.chdir('/home/amp')
    call(['docker-compose', '-f /home/amp/src/grlc-dev/docker-compose.default.yml', 'restart'])
    print "All done; exiting..."

if __name__ == '__main__':
    update()
    exit(0)
