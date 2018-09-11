#!/usr/bin/env python

from flask import Flask
from subprocess import call
import os
app = Flask(__name__)

@app.route("/", methods=['POST'])
def update():
    print "Starting image update"
    call(['docker', 'pull', 'clariah/grlc:dev'])
    call(['docker-compose', '-f', '/home/amp/src/grlc-dev/docker-compose.default.yml', 'restart'])
    print "All done; exiting..."

    return 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004, debug=True)
