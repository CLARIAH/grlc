#!/usr/bin/env python

# grlc.py: the grlc server

from flask import Flask, request, jsonify, render_template, make_response
import requests
import logging
import re
from rdflib import Graph

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

# Server routes
@app.route('/')
def hello():
    resp = make_response(render_template('index.html'))
    return resp

@app.route('/api/<user>/<repo>/<query_name>', methods=['GET'])
@app.route('/api/<user>/<repo>/<query_name>.<content>', methods=['GET'])
def query(user, repo, query_name, content=None):
    glogger.debug("-----> Executing call name at /{}/{}/{}".format(user, repo, query_name))
    glogger.debug("Request accept header: " + request.headers["Accept"])
    raw_repo_uri = static.GITHUB_RAW_BASE_URL + user + '/' + repo + '/master/'

    # The URIs of all candidates
    raw_sparql_query_uri = raw_repo_uri + query_name + '.rq'
    raw_alt_sparql_query_uri = raw_repo_uri + query_name + '.sparql'
    raw_tpf_query_uri = raw_repo_uri + query_name + '.tpf'

    raw_sparql_query = requests.get(raw_sparql_query_uri)
    raw_alt_sparql_query = requests.get(raw_alt_sparql_query_uri)
    raw_tpf_query = requests.get(raw_tpf_query_uri)

    # Call name implemented with SPARQL query
    if raw_sparql_query.status_code == 200 or raw_alt_sparql_query.status_code == 200:
        if raw_sparql_query.status_code == 200:
            raw_sparql_query = raw_sparql_query.text
        else:
            raw_sparql_query = raw_alt_sparql_query.text

        endpoint = gquery.guess_endpoint_uri(raw_sparql_query, raw_repo_uri)
        glogger.debug("=====================================================")
        glogger.debug("Sending query to SPARQL endpoint: {}".format(endpoint))
        glogger.debug("=====================================================")

        query_metadata = gquery.get_metadata(raw_sparql_query)

        pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""

        # Rewrite query using parameter values
        rewritten_query = gquery.rewrite_query(raw_sparql_query, request.args, endpoint)

        # Rewrite query using pagination
        paginated_query = gquery.paginate_query(rewritten_query, request.args)

        resp = None
        # If we have a mime field, we load the remote dump and query it locally
        if 'mime' in query_metadata and query_metadata['mime']:
            g = Graph()
            try:
                query_metadata = gquery.get_metadata(raw_sparql_query)
                g.parse(endpoint, format=query_metadata['mime'])
            except Exception as e:
                glogger.error(e)
            results = g.query(paginated_query, result='sparql')
            # glogger.debug("Results of SPARQL query against locally loaded dump:")
            # Prepare return format as requested
            resp_string = ""
            # glogger.debug("Requested formats: {}".format(request.headers['Accept']))
            # if content:
            #     glogger.debug("Requested formats from extension: {}".format(static.mimetypes[content]))
            if 'application/json' in request.headers['Accept'] or (content and 'application/json' in static.mimetypes[content]):
                resp_string = results.serialize(format='json')
            elif 'text/csv' in request.headers['Accept'] or (content and 'text/csv' in static.mimetypes[content]):
                resp_string = results.serialize(format='csv')
            # elif 'text/html' in request.headers['Accept']:
            #     resp_string = results.serialize(format='html')
            else:
                return 'Unacceptable requested format', 415
            del g

            resp = make_response(resp_string)
        # If there's no mime type, the endpoint is an actual SPARQL endpoint
        else:
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
    # Call name implemented with TPF query
    elif raw_tpf_query.status_code == 200:
        raw_tpf_query = raw_tpf_query.text
        endpoint = gquery.guess_endpoint_uri(raw_tpf_query, raw_repo_uri)
        glogger.debug("=====================================================")
        glogger.debug("Sending query to TPF endpoint: {}".format(endpoint))
        glogger.debug("=====================================================")

        query_metadata = gquery.get_yaml_decorators(raw_tpf_query)

        # TODO: pagination for TPF

        # Preapre HTTP request
        headers = { 'Accept' : request.headers['Accept'] }
        if content:
            headers = { 'Accept' : static.mimetypes[content] }
        tpf_list = re.split('\n|=', raw_tpf_query)
        subject = tpf_list[tpf_list.index('subject') + 1]
        predicate = tpf_list[tpf_list.index('predicate') + 1]
        object = tpf_list[tpf_list.index('object') + 1]
        data = { 'subject' : subject, 'predicate' : predicate, 'object' : object}

        response = requests.get(endpoint, params=data, headers=headers)
        glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

        # Response headers
        resp = make_response(response.text)
        resp.headers['Server'] = 'grlc/1.0.0'
        resp.headers['Content-Type'] = response.headers['Content-Type']

        return resp
    else:
        return "Couldn't find a SPARQL, RDF dump, or TPF query with the requested name", 404


@app.route('/api/<user>/<repo>', strict_slashes=False)
@app.route('/api/<user>/<repo>/api-docs')
def api_docs(user, repo):
    return render_template('api-docs.html', user=user, repo=repo)

@app.route('/api/<user>/<repo>/spec', methods=['GET'])
def swagger_spec(user, repo, content=None):
    glogger.info("-----> Generating swagger spec for /{}/{}".format(user,repo))

    swag = utils.build_swagger_spec(user, repo, app.config['SERVER_NAME'])

    resp_spec = make_response(jsonify(swag))
    resp_spec.headers['Content-Type'] = 'application/json'

    if 'text/turtle' in request.headers['Accept']:
        resp_spec = make_response(utils.turtleize(swag))
        resp_spec.headers['Content-Type'] = 'text/turtle'

    resp_spec.headers['Cache-Control'] = static.CACHE_CONTROL_POLICY # Caching JSON specs for 15 minutes

    glogger.info("-----> API spec generation for /{}/{} complete".format(user, repo))

    return resp_spec


if __name__ == '__main__':
    app.run(host=static.DEFAULT_HOST, port=static.DEFAULT_PORT, debug=True)
