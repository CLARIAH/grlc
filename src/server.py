#!/usr/bin/env python

# server.py: the grlc server

from flask import Flask, request, jsonify, render_template, make_response
import requests
import logging
import re
from rdflib import Graph
from github import Github

# grlc modules
import static as static
import gquery as gquery
import utils as utils
import sparql as sparql
from prov import grlcPROV

from fileLoaders import GithubLoader, LocalLoader

# The Flask app
app = Flask(__name__)

# Set logging format
logging.basicConfig(level=logging.DEBUG, format=static.LOG_FORMAT)
app.debug_log_format = static.LOG_FORMAT
glogger = logging.getLogger(__name__)

# Server routes
@app.route('/')
def grlc():
    resp = make_response(render_template('index.html'))
    return resp

@app.route('/api/local/local/<query_name>', methods=['GET'])
def query_local(query_name):
    return query(user=None, repo=None, query_name=query_name)

from queryTypes import qType

@app.route('/api/<user>/<repo>/<query_name>', methods=['GET', 'POST'])
@app.route('/api/<user>/<repo>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api/<user>/<repo>/commit/<sha>/<query_name>', methods=['GET', 'POST'])
@app.route('/api/<user>/<repo>/commit/<sha>/<query_name>.<content>', methods=['GET', 'POST'])
def query(user, repo, query_name, sha=None, content=None):
    glogger.debug("-----> Executing call name at /{}/{}/{} on commit {}".format(user, repo, query_name, sha))
    glogger.debug("Request accept header: " + request.headers["Accept"])

    if user is None and repo is None:
        loader = LocalLoader()
    else:
        loader = GithubLoader(user, repo, sha, None)

    query, q_type = loader.getTextForName(query_name)

    # Call name implemented with SPARQL query
    if q_type == qType['SPARQL']:
        raw_sparql_query = query

        endpoint, auth = gquery.guess_endpoint_uri(raw_sparql_query, loader)
        if endpoint=='':
            return 'No SPARQL endpoint indicated', 407

        glogger.debug("=====================================================")
        glogger.debug("Sending query to SPARQL endpoint: {}".format(endpoint))
        glogger.debug("=====================================================")

        query_metadata = gquery.get_metadata(raw_sparql_query, endpoint)

        pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""

        rewritten_query = query_metadata['query']

        # Rewrite query using parameter values
        if query_metadata['type'] == 'SelectQuery' or query_metadata['type'] == 'ConstructQuery':
            rewritten_query = gquery.rewrite_query(query_metadata['query'], query_metadata['parameters'], request.args)

        # Rewrite query using pagination
        if query_metadata['type'] == 'SelectQuery' and 'pagination' in query_metadata:
            rewritten_query = gquery.paginate_query(rewritten_query, query_metadata['pagination'], request.args)

        resp = None
        # If we have a mime field, we load the remote dump and query it locally
        if 'mime' in query_metadata and query_metadata['mime']:
            glogger.debug("Detected {} MIME type, proceeding with locally loading remote dump".format(query_metadata['mime']))
            g = Graph()
            try:
                query_metadata = gquery.get_metadata(raw_sparql_query, endpoint)
                g.parse(endpoint, format=query_metadata['mime'])
                glogger.debug("Local RDF graph loaded successfully with {} triples".format(len(g)))
            except Exception as e:
                glogger.error(e)
            results = g.query(rewritten_query, result='sparql')
            # Prepare return format as requested
            resp_string = ""
            # glogger.debug("Requested formats: {}".format(request.headers['Accept']))
            # if content:
            #     glogger.debug("Requested formats from extension: {}".format(static.mimetypes[content]))
            if 'application/json' in request.headers['Accept'] or (content and 'application/json' in static.mimetypes[content]):
                resp_string = results.serialize(format='json')
                glogger.debug("Results of SPARQL query against locally loaded dump: {}".format(resp_string))
            elif 'text/csv' in request.headers['Accept'] or (content and 'text/csv' in static.mimetypes[content]):
                resp_string = results.serialize(format='csv')
                glogger.debug("Results of SPARQL query against locally loaded dump: {}".format(resp_string))
            # elif 'text/html' in request.headers['Accept']:
            #     resp_string = results.serialize(format='html')
            else:
                return 'Unacceptable requested format', 415
            glogger.debug("Finished processing query against RDF dump, end of use case")
            del g

            return make_response(resp_string)
        # Check for INSERT/POST
        if query_metadata['type'] == 'InsertData':
            glogger.info("Processing INSERT query")
            # Rewrite INSERT
            rewritten_query = rewritten_query.replace("?_g_iri", "{}".format(request.form.get('g')))
            rewritten_query = rewritten_query.replace("<s> <p> <o>", request.form.get('data'))
            glogger.info("INSERT query rewritten as {}".format(rewritten_query))

            # Prepare HTTP POST request
            headers = { 'Accept' : request.headers['Accept'], 'Content-Type' : 'application/sparql-update' }
            # data = { 'query' : rewritten_query }

            response = requests.post(endpoint, data=rewritten_query, headers=headers, auth=auth)
            glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

            # Response headers
            resp = make_response(response.text)
            resp.headers['Server'] = 'grlc/1.0.0'
            resp.headers['Content-Type'] = response.headers['Content-Type']

        # If there's no mime type, the endpoint is an actual SPARQL endpoint
        else:
            # requestedMimeType = static.mimetypes[content] if content else request.headers['Accept']
            # glogger.debug('Requested MIME type: {}'.format(requestedMimeType))
            # result, contentType = sparql.getResponseText(endpoint, query, requestedMimeType)
            #
            # Response headers
            # resp = make_response(result)
            # resp.headers['Server'] = 'grlc/1.0.0'
            # resp.headers['Content-Type'] = contentType

            # Prepare HTTP request
            headers = { 'Accept' : request.headers['Accept'] }
            if content:
                # headers = { 'Accept' : static.mimetypes[content] , 'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}
                headers = { 'Accept' : static.mimetypes[content]}
            data = { 'query' : rewritten_query }

            glogger.debug('Sending HTTP request to SPARQL endpoint with params: {}'.format(data))
            glogger.debug('Sending HTTP request to SPARQL endpoint with headers: {}'.format(headers))
            glogger.debug('Sending HTTP request to SPARQL endpoint with auth: {}'.format(auth))
            response = requests.get(endpoint, params=data, headers=headers, auth=auth)
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
    elif q_type == qType['TPF']:
        raw_tpf_query = query
        endpoint, auth = gquery.guess_endpoint_uri(raw_tpf_query, loader)
        glogger.debug("=====================================================")
        glogger.debug("Sending query to TPF endpoint: {}".format(endpoint))
        glogger.debug("=====================================================")

        query_metadata = gquery.get_yaml_decorators(raw_tpf_query)

        # TODO: pagination for TPF

        # Preapre HTTP request
        headers = { 'Accept' : request.headers['Accept'] , 'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}
        if content:
            headers = { 'Accept' : static.mimetypes[content] , 'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}
        tpf_list = re.split('\n|=', raw_tpf_query)
        subject = tpf_list[tpf_list.index('subject') + 1]
        predicate = tpf_list[tpf_list.index('predicate') + 1]
        object = tpf_list[tpf_list.index('object') + 1]
        data = { 'subject' : subject, 'predicate' : predicate, 'object' : object}

        response = requests.get(endpoint, params=data, headers=headers, auth=auth)
        glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

        # Response headers
        resp = make_response(response.text)
        resp.headers['Server'] = 'grlc/1.0.0'
        resp.headers['Content-Type'] = response.headers['Content-Type']

        return resp
    else:
        return "Couldn't find a SPARQL, RDF dump, or TPF query with the requested name", 404


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
    glogger.info("-----> Generating swagger spec for /{}/{} on commit {}".format(user,repo,sha))

    # Init provenance recording
    if user is not None and repo is not None:
        prov_g = grlcPROV(user, repo)
        gh = Github(static.ACCESS_TOKEN)
        gh_repo = gh.get_repo(user + '/' + repo)
    else:
        prov_g = None
        gh_repo = None

    swag = utils.build_swagger_spec(user, repo, sha, static.SERVER_NAME, prov_g, gh_repo)

    if user is not None and repo is not None:
        prov_g.end_prov_graph()
        swag['prov'] = prov_g.serialize(format='turtle')
    # prov_g.log_prov_graph()

    resp_spec = make_response(jsonify(swag))
    resp_spec.headers['Content-Type'] = 'application/json'

    if 'text/turtle' in request.headers['Accept']:
        resp_spec = make_response(utils.turtleize(swag))
        resp_spec.headers['Content-Type'] = 'text/turtle'

    resp_spec.headers['Cache-Control'] = static.CACHE_CONTROL_POLICY # Caching JSON specs for 15 minutes

    glogger.info("-----> API spec generation for /{}/{} on commit {} complete".format(user, repo, sha))

    return resp_spec

if __name__ == '__main__':
    app.run(host=static.DEFAULT_HOST, port=static.DEFAULT_PORT, debug=True)
