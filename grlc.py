#!/usr/bin/env python

# grlc.py: the grlc server

from flask import Flask, request, jsonify, json, render_template, make_response
import urllib
import urllib2
import json
import StringIO
import logging
import re

import traceback
import cgi
import datetime

# grlc modules
import src.static as static
import src.cache as cache
import src.gquery as gquery
import src.util as util

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
    resp.headers['Cache-Control'] = 'public, max-age=43200'
    return resp
    #return render_template('index.html')

@app.route('/grlc/<user>/<repo>/<query_name>', methods=['GET'])
@app.route('/grlc/<user>/<repo>/<query_name>.<content>', methods=['GET'])
def query(user, repo, query_name, content=None):
    glogger.debug("Got request at endpoint /" + user + "/" + repo + "/" + query_name)
    glogger.debug("Request accept header: " +request.headers["Accept"])
    raw_repo_uri = static.GITHUB_RAW_BASE_URL + user + '/' + repo + '/master/'
    raw_query_uri = raw_repo_uri + query_name + '.rq'
    stream = urllib2.urlopen(raw_query_uri)
    raw_query = stream.read()

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
        headers = { 'Accept' : mimetypes[content] }
    data = { 'query' : paginated_query }

    data_encoded = urllib.urlencode(data)
    req = urllib2.Request(endpoint, data_encoded, headers)
    glogger.debug("Sending request: " + req.get_full_url() + "?" + req.get_data())
    response = urllib2.urlopen(req)
    glogger.debug('Response header from endpoint: ' + response.info().getheader('Content-Type'))

    # Response headers
    resp = make_response(response.read())
    resp.headers['Server'] = 'grlc/1.0.0'
    resp.headers['Content-Type'] = response.info().getheader('Content-Type')
    # If the query is paginated, set link HTTP headers
    if pagination:
        # Get number of total results
        count = gquery.count_query_results(query, endpoint)
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

@app.route('/grlc/<user>/<repo>/api-docs')
def api_docs(user, repo):
    return render_template('api-docs.html', user=user, repo=repo)


@app.route('/grlc/<user>/<repo>/spec')
def swagger_spec(user, repo):
    glogger.info("Generating swagger spec for /" + user + "/" + repo)
    api_repo_uri = static.GITHUB_API_BASE_URL + user + '/' + repo
    # Check if we have an updated cached spec for this repo
    # if cache.is_cache_updated(cache_obj, api_repo_uri):
    #     glogger.info("Reusing updated cache for this spec")
    #     return jsonify(cache_obj[api_repo_uri]['spec'])
    stream = urllib2.urlopen(api_repo_uri)
    resp = json.load(stream)
    swag = {}
    swag['swagger'] = '2.0'
    swag['info'] = {'version': '1.0', 'title': resp['name'], 'contact': {'name': resp['owner']['login'], 'url': resp['owner']['html_url']}, 'license': {'name' : 'License', 'url': static.GITHUB_RAW_BASE_URL + user + '/' + repo + '/master/LICENSE'}}
    swag['host'] = app.config['SERVER_NAME']
    swag['basePath'] = '/grlc/' + user + '/' + repo + '/'
    swag['schemes'] = ['http']
    swag['paths'] = {}

    api_repo_content_uri = api_repo_uri + '/contents'
    stream = urllib2.urlopen(api_repo_content_uri)
    resp = json.load(stream)
    # Fetch all .rq files
    for c in resp:
        if ".rq" in c['name']:
            call_name = c['name'].split('.')[0]
            # Retrieve extra metadata from the query decorators
            raw_repo_uri = static.GITHUB_RAW_BASE_URL + user + '/' + repo + '/master/'
            raw_query_uri = raw_repo_uri + c['name']
            stream = urllib2.urlopen(raw_query_uri)
            resp = stream.read()

            glogger.info("Processing query " + raw_query_uri)

            try:
                query_metadata = gquery.get_metadata(resp)
            except Exception as e:
                glogger.error("Could not parse query at {}".format(raw_query_uri))
                glogger.error(e)
                continue

            tags = query_metadata['tags'] if 'tags' in query_metadata else []
            glogger.debug("Read query tags: " + ', '.join(tags))

            summary = query_metadata['summary'] if 'summary' in query_metadata else ""
            glogger.debug("Read query summary: " + summary)

            description = query_metadata['description'] if 'description' in query_metadata else ""
            glogger.debug("Read query description: " + description)

            method = query_metadata['method'].lower() if 'method' in query_metadata else "get"
            if method not in ['get', 'post', 'head', 'put', 'delete', 'options', 'connect']:
                method = "get"

            pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""
            glogger.debug("Read query pagination: " + str(pagination))

            # endpoint = query_metadata['endpoint'] if 'endpoint' in query_metadata else ""
            endpoint = gquery.guess_endpoint_uri("", raw_repo_uri)
            glogger.debug("Read query endpoint: " + endpoint)

            try:
                parameters = gquery.get_parameters(query_metadata['query'], endpoint)
            except Exception as e:
                print traceback.print_exc()

                glogger.error("Could not parse parameters of query {}".format(raw_query_uri))
                continue

            glogger.debug("Read request parameters")
            glogger.debug(parameters)
            # TODO: do something intelligent with the parameters!
            # As per #3, prefetching IRIs via SPARQL and filling enum

            params = []
            for v, p in parameters.items():
                param = {}
                param['name'] = p['name']
                param['type'] = "string"
                param['required'] = p['required']
                param['in'] = "query"
                param['enum'] = p['enum']
                param['description'] = "A value of type {} that will substitute {} in the original query".format(p['type'], p['original'])

                params.append(param)

            # If this query allows pagination, add page number as parameter
            if pagination:
                pagination_param = {}
                pagination_param['name'] = "page"
                pagination_param['type'] = "int"
                pagination_param['in'] = "query"
                pagination_param['description'] = "The page number for this paginated query ({} results per page)".format(pagination)

                params.append(pagination_param)

            item_properties = {}
            if query_metadata['type'] != 'SelectQuery':
                # TODO: Turn this into a nicer thingamajim
                glogger.warning("This is not a SelectQuery, don't really know what to do!")
                summary += "WARNING: non-SELECT queries are not really treated properly yet"
                # just continue with empty item_properties
            else:
                # We now know it is a SELECT query
                for pv in query_metadata['variables']:
                    i = {
                        "name": pv,
                        "type": "object",
                        "required": ["type", "value"],
                        "properties": {
                            "type": {
                                "type": "string"
                            },
                            "value": {
                                "type": "string"
                            },
                            "xml:lang": {
                                "type": "string"
                            },
                            "datatype": {
                                "type": "string"
                            }
                        }
                    }


                    item_properties[pv] = i

            swag['paths'][call_name] = {}
            swag['paths'][call_name][method] = {"tags" : tags,
                                               "summary" : summary,
                                               "description" : description + "\n<pre>\n{}\n</pre>".format(cgi.escape(query_metadata['query'])),
                                               "produces" : ["text/csv", "application/json", "text/html"],
                                               "parameters": params,
                                               "responses": {
                                                   "200" : {
                                                       "description" : "SPARQL query response",
                                                       "schema" : {
                                                           "type" : "array",
                                                           "items": {
                                                                "type": "object",
                                                                "properties": item_properties
                                                            },
                                                           }
                                                       },
                                                   "default" : {
                                                       "description" : "Unexpected error",
                                                       "schema" : {
                                                           "$ref" : "#/definitions/Message"
                                                       }
                                                   }
                                               }
                                               }
    # Store the generated spec in the cache
    # cache_obj[api_repo_uri] = {'date' : json.dumps(datetime.datetime.now(), default=util.date_handler).split('\"')[1], 'spec' : swag}
    # with open(cache.CACHE_NAME, 'w') as cache_file:
    #     json.dump(cache_obj, cache_file)
    # glogger.debug("Local cache updated")

    resp_spec = make_response(jsonify(swag))
    resp_spec.headers['Cache-Control'] = 'public, max-age=900' # Caching JSON specs for 15 minutes
    return resp_spec

    # return jsonify(swag)

# TODO: Issue #23 - catch GitHub webhook POST to auto-update spec cache
# @app.route('/sparql', methods = ['POST'])
# def github_push():
#         return 'foo'

if __name__ == '__main__':
    app.run(port=8088, debug=True)
