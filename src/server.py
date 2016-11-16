#!/usr/bin/env python

# grlc.py: the grlc server

from flask import Flask, request, jsonify, render_template, make_response
import requests
import logging
import re

# grlc modules
import static as static
import gquery as gquery
import utils as utils

# The Flask app
app = Flask(__name__)

# Set logging format
logging.basicConfig(level=logging.DEBUG, format=static.LOG_FORMAT)
app.debug_log_format = static.LOG_FORMAT
glogger = logging.getLogger(__name__)

# Initialize cache
# cache_obj = cache.init_cache()

# Server routes
@app.route('/')
def hello():
    resp = make_response(render_template('index.html'))
    #resp.headers['Cache-Control'] = 'public, max-age=43200'
    return resp

@app.route('/api/<user>/<repo>/<query_name>', methods=['GET'])
@app.route('/api/<user>/<repo>/<query_name>.<content>', methods=['GET'])
def query(user, repo, query_name, content=None):
    glogger.debug("Got request at endpoint /" + user + "/" + repo + "/" + query_name)
    glogger.debug("Request accept header: " +request.headers["Accept"])
    raw_repo_uri = static.GITHUB_RAW_BASE_URL + user + '/' + repo + '/master/'
    raw_query_uri = raw_repo_uri + query_name + '.rq'
    raw_query = requests.get(raw_query_uri).text

    endpoint = gquery.guess_endpoint_uri(raw_query, raw_repo_uri)
    glogger.debug("Sending query to endpoint: " + endpoint)

    query_metadata = gquery.get_metadata(raw_query)
    pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""

    # Rewrite query using parameter values
    rewritten_query = gquery.rewrite_query(raw_query, request.args, endpoint)

    # Rewrite query using pagination
    paginated_query = gquery.paginate_query(rewritten_query, request.args)

    # Preapre HTTP request
    headers = { 'Accept' : request.headers['Accept'] }
    if content:
        headers = { 'Accept' : static.mimetypes[content] }
    data = { 'query' : paginated_query }

    response = requests.get(endpoint, params=data, headers=headers)
    glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

    # Response headers
    resp = make_response(response.text)
    resp.headers['Server'] = 'grlc/1.0.0'
    resp.headers['Content-Type'] = response.headers['Content-Type']
    # If the query is paginated, set link HTTP headers
    if pagination:
        # Get number of total results
        count = gquery.count_query_results(rewritten_query, endpoint)
        page = 1
        if 'page' in request.args:
            page = int(request.args['page'])
            next_url = re.sub("page=[0-9]+", "page={}".format(page + 1), request.url)
            prev_url = re.sub("page=[0-9]+", "page={}".format(page - 1), request.url)
            first_url = re.sub("page=[0-9]+", "page=1", request.url)
            last_url = re.sub("page=[0-9]+", "page={}".format(count / pagination), request.url)
        else:
            next_url = request.url + "?page={}".format(page + 1)
            prev_url = request.url + "?page={}".format(page - 1)
            first_url = request.url + "?page={}".format(page)
            last_url = request.url + "?page={}".format(count / pagination)
        if page == 1:
            resp.headers['Link'] = "<{}>; rel=next, <{}>; rel=last".format(next_url, last_url)
        elif page == count / pagination:
            resp.headers['Link'] = "<{}>; rel=prev, <{}>; rel=first".format(prev_url, first_url)
        else:
            resp.headers['Link'] = "<{}>; rel=next, <{}>; rel=prev, <{}>; rel=first, <{}>; rel=last".format(next_url, prev_url, first_url, last_url)

    return resp

@app.route('/api/<user>/<repo>')
@app.route('/api/<user>/<repo>/')
@app.route('/api/<user>/<repo>/api-docs')
def api_docs(user, repo):
    return render_template('api-docs.html', user=user, repo=repo)

@app.route('/api/<user>/<repo>/api-docs-default')
def api_docs_default(user, repo):
    return render_template('api-docs-default.html', user=user, repo=repo)

@app.route('/api/<user>/<repo>/spec')
def swagger_spec(user, repo):
    glogger.info("Generating swagger spec for /" + user + "/" + repo)

    swag = utils.build_swagger_spec(user, repo, app.config['SERVER_NAME'])

    # Store the generated spec in the cache
    # cache_obj[api_repo_uri] = {'date' : json.dumps(datetime.datetime.now(), default=util.date_handler).split('\"')[1], 'spec' : swag}
    # with open(cache.CACHE_NAME, 'w') as cache_file:
    #     json.dump(cache_obj, cache_file)
    # glogger.debug("Local cache updated")

    resp_spec = make_response(jsonify(swag))
    resp_spec.headers['Cache-Control'] = 'public, max-age=900' # Caching JSON specs for 15 minutes
    return resp_spec

@app.route('/api/<user>/<repo>/spec-default')
def swagger_spec_default(user, repo):
    glogger.info("Generating default spec for /" + user + "/" + repo)

    swag = utils.build_swagger_spec(user, repo, app.config['SERVER_NAME'], default=True)

    resp_spec = make_response(jsonify(swag))
    resp_spec.headers['Cache-Control'] = 'public, max-age=900' # Caching JSON specs for 15 minutes
    return resp_spec

# TODO: Issue #23 - catch GitHub webhook POST to auto-update spec cache
# @app.route('/sparql', methods = ['POST'])
# def github_push():
#         return 'foo'

if __name__ == '__main__':
    app.run(port=8088, debug=True)
