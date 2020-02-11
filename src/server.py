#!/usr/bin/env python

# server.py: the grlc server

from flask import Flask, request, jsonify, render_template, make_response

# grlc modules
import grlc.static as static
import grlc.utils as utils
import grlc.glogging as glogging

glogger = glogging.getGrlcLogger(__name__)

### The Flask app ###
app = Flask(__name__)

### Server routes ###
@app.route('/')
def grlc():
    resp = make_response(render_template('index.html'))
    return resp

#############################
### Routes for local APIs ###
#############################

# Spec generation, front-end
@app.route('/api-local', methods=['GET'], strict_slashes=False)
def api_docs_local():
    return render_template('api-docs.html', swagger_url='/api-local/swagger')

# Spec generation, JSON
@app.route('/api-local/swagger', methods=['GET'])
def swagger_local():
    return swagger_spec(user=None, repo=None, sha=None, content=None)

# Callname execution
@app.route('/api-local/<query_name>', methods=['GET'])
def query_local(query_name):
    return query(user=None, repo=None, query_name=query_name)


################################
### Routes for URL HTTP APIs ###
################################

# Callname execution
@app.route('/api-url/<query_name>', methods=['GET'])
def query_param(query_name):
    spec_url = request.args['specUrl']
    glogger.debug("Spec URL: ".format(spec_url))
    return query(user=None, repo=None, query_name=query_name, spec_url=spec_url)

# Spec generation, front-end
@app.route('/api-url', methods=['POST', 'GET'], strict_slashes=False)
def api_docs_param():
    # Get queries provided by params
    spec_url = request.args['specUrl']
    glogger.info("Spec URL: ".format(spec_url))
    return render_template('api-docs.html', swagger_url='/api-url/swagger?specUrl=' + spec_url)

# Spec generation, JSON
@app.route('/api-url/swagger', methods=['GET'])
def swagger_spec_param():
    spec_url = request.args['specUrl']
    glogger.info("Spec URL: ".format(spec_url))
    return swagger_spec(user=None, repo=None, spec_url=spec_url)


##############################
### Routes for GitHub APIs ###
##############################

# Callname execution
@app.route('/api-git/<user>/<repo>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-git/<user>/<repo>/<subdir>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-git/<user>/<repo>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-git/<user>/<repo>/<subdir>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-git/<user>/<repo>/commit/<sha>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-git/<user>/<repo>/<subdir>/commit/<sha>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-git/<user>/<repo>/commit/<sha>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-git/<user>/<repo>/<subdir>/commit/<sha>/<query_name>.<content>', methods=['GET', 'POST'])
def query(user, repo, query_name, subdir=None, spec_url=None, sha=None, content=None):
    glogger.info("-----> Executing call name at /{}/{}/{}/{} on commit {}".format(user, repo, subdir, query_name, sha))
    glogger.debug("Request accept header: " + request.headers["Accept"])

    requestArgs = request.args
    acceptHeader = request.headers['Accept']
    requestUrl = request.url
    formData = request.form

    query_response, status, headers = utils.dispatch_query(user, repo, query_name, subdir, spec_url,
                                                           sha=sha, content=content, requestArgs=requestArgs,
                                                           acceptHeader=acceptHeader,
                                                           requestUrl=requestUrl, formData=formData)

    if isinstance(query_response, list):
        query_response = jsonify(query_response)

    return make_response(query_response, status, headers)

# Spec generation, front-end
@app.route('/api-git/<user>/<repo>', strict_slashes=False)
@app.route('/api-git/<user>/<repo>/<subdir>', strict_slashes=False)
@app.route('/api-git/<user>/<repo>/api-docs')
@app.route('/api-git/<user>/<repo>/commit/<sha>')
@app.route('/api-git/<user>/<repo>/commit/<sha>/api-docs')
@app.route('/api-git/<user>/<repo>/<subdir>/commit/<sha>')
@app.route('/api-git/<user>/<repo>/<subdir>/commit/<sha>/api-docs')
def api_docs(user, repo, subdir=None, spec_url=None, sha=None):
    swagger_url = '/api-git/{}/{}'.format(user, repo)
    if subdir:
        swagger_url += '/{}'.format(subdir)
    if sha:
        swagger_url += '/commit/{}'.format(sha)
    swagger_url += '/swagger'
    return render_template('api-docs.html', swagger_url=swagger_url)

# Spec generation, JSON
@app.route('/api-git/<user>/<repo>/swagger', methods=['GET'])
@app.route('/api-git/<user>/<repo>/<subdir>/swagger', methods=['GET'])
@app.route('/api-git/<user>/<repo>/commit/<sha>/swagger')
@app.route('/api-git/<user>/<repo>/<subdir>/commit/<sha>/swagger')
def swagger_spec(user, repo, subdir=None, spec_url=None, sha=None, content=None):
    glogger.info("-----> Generating swagger spec for /{}/{}, subdir {}, params {}, on commit {}".format(user, repo, subdir, spec_url, sha))

    swag = utils.build_swagger_spec(user, repo, subdir, spec_url, sha, static.SERVER_NAME)

    if 'text/turtle' in request.headers['Accept']:
        resp_spec = make_response(utils.turtleize(swag))
        resp_spec.headers['Content-Type'] = 'text/turtle'
    else:
        resp_spec = make_response(jsonify(swag))
        resp_spec.headers['Content-Type'] = 'application/json'

    resp_spec.headers['Cache-Control'] = static.CACHE_CONTROL_POLICY  # Caching JSON specs for 15 minutes

    glogger.info("-----> API spec generation for /{}/{}, subdir {}, params {}, on commit {} complete".format(user, repo, subdir, spec_url, sha))
    return resp_spec



# Main thread
if __name__ == '__main__':
    app.run(host=static.DEFAULT_HOST, port=static.DEFAULT_PORT, debug=True)
