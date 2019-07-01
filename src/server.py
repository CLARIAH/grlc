#!/usr/bin/env python

# server.py: the grlc server

from flask import Flask, request, jsonify, render_template, make_response
import logging

# grlc modules
import grlc.static as static
import grlc.utils as utils

# The Flask app
app = Flask(__name__)

# Set logging format
glogger = logging.getLogger(__name__)


# Server routes
@app.route('/')
def grlc():
    resp = make_response(render_template('index.html'))
    return resp


@app.route('/api/local/local/<query_name>', methods=['GET'])
def query_local(query_name):
    return query(user=None, repo=None, query_name=query_name)

# http://grlc.io/api/url
# get/post: url-query:  https://api.druid.datalegend.net/datasets/IISG/iisg-kg/queries/rosa-luxemburg-gallery/1

# http://grlc.io/api/url/exec


@app.route('/api/<user>/<repo>/<query_name>', methods=['GET', 'POST'])
@app.route('/api/<user>/<repo>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api/<user>/<repo>/commit/<sha>/<query_name>', methods=['GET', 'POST'])
@app.route('/api/<user>/<repo>/commit/<sha>/<query_name>.<content>', methods=['GET', 'POST'])
def query(user, repo, query_name, sha=None, content=None):
    glogger.info("-----> Executing call name at /{}/{}/{} on commit {}".format(user, repo, query_name, sha))
    glogger.debug("Request accept header: " + request.headers["Accept"])

    requestArgs = request.args
    acceptHeader = request.headers['Accept']
    requestUrl = request.url
    formData = request.form

    query_response, status, headers = utils.dispatch_query(user, repo, query_name,
                                                           sha=sha, content=content, requestArgs=requestArgs,
                                                           acceptHeader=acceptHeader,
                                                           requestUrl=requestUrl, formData=formData)

    if isinstance(query_response, list):
        query_response = jsonify(query_response)

    return make_response(query_response, status, headers)


@app.route('/api/local', methods=['GET'])
def api_docs_local():
    return api_docs(user='local', repo='local', sha=None)


@app.route('/api/local/local/spec', methods=['GET'])
def swagger_spec_local():
    return swagger_spec(user=None, repo=None, sha=None, content=None)


@app.route('/api/<user>/<repo>', strict_slashes=False)
@app.route('/api/<user>/<repo>/api-docs')
@app.route('/api/<user>/<repo>/commit/<sha>')
@app.route('/api/<user>/<repo>/commit/<sha>/api-docs')
def api_docs(user, repo, sha=None):
    return render_template('api-docs.html', user=user, repo=repo, sha=sha)


@app.route('/api/<user>/<repo>/spec', methods=['GET'])
@app.route('/api/<user>/<repo>/commit/<sha>/spec')
def swagger_spec(user, repo, sha=None, content=None):
    glogger.info("-----> Generating swagger spec for /{}/{} on commit {}".format(user, repo, sha))

    swag = utils.build_swagger_spec(user, repo, sha, static.SERVER_NAME)

    if 'text/turtle' in request.headers['Accept']:
        resp_spec = make_response(utils.turtleize(swag))
        resp_spec.headers['Content-Type'] = 'text/turtle'
    else:
        resp_spec = make_response(jsonify(swag))
        resp_spec.headers['Content-Type'] = 'application/json'

    resp_spec.headers['Cache-Control'] = static.CACHE_CONTROL_POLICY  # Caching JSON specs for 15 minutes

    glogger.info("-----> API spec generation for /{}/{} on commit {} complete".format(user, repo, sha))
    return resp_spec


if __name__ == '__main__':
    app.run(host=static.DEFAULT_HOST, port=static.DEFAULT_PORT, debug=static.LOG_DEBUG_MODE)
