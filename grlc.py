#!/usr/bin/env python

from flask import Flask, request, jsonify, json, render_template, make_response
import urllib
import urllib2
import json
import StringIO
import logging
import re
import yaml
from rdflib.plugins.sparql.parser import Query
from rdflib.plugins.sparql.processor import translateQuery
from pyparsing import ParseException
import traceback
import cgi
import datetime

CACHE_NAME = "db.json"

XSD_DATATYPES = ["decimal", "float", "double", "integer", "positiveInteger", "negativeInteger", "nonPositiveInteger", "nonNegativeInteger", "long", "int", "short", "byte", "unsignedLong", "unsignedInt", "unsignedShort", "unsignedByte", "dateTime", "date", "gYearMonth", "gYear", "duration", "gMonthDay", "gDay", "gMonth", "string", "normalizedString", "token", "language", "NMTOKEN", "NMTOKENS", "Name", "NCName", "ID", "IDREFS", "ENTITY", "ENTITIES", "QName", "boolean", "hexBinary", "base64Binary", "anyURI", "notation"]

mimetypes = {
    'csv' : 'text/csv; q=1.0, */*; q=0.1',
    'json' : 'application/json; q=1.0, application/sparql-results+json; q=0.8, */*; q=0.1',
    'html' : 'text/html; q=1.0, */*; q=0.1'
}

app = Flask(__name__)

# Logging format
FORMAT = '%(asctime)-15s [%(levelname)s] (%(funcName)s) %(message)s'
app.debug_log_format = FORMAT

# Initialize cache
cache = json.loads("{}")
try:
    with open(CACHE_NAME, 'r') as cache_file:
        try:
            cache = json.load(cache_file)
        except ValueError:
            print "The cache file seems to be empty, starting with flushed cache"
except IOError:
    print "The cache file seems to be empty, starting with flushed cache"

print "Loaded JSON cache"

def guess_endpoint_uri(rq, ru):
    '''
    Guesses the endpoint URI from (in this order):
    - An #+endpoint decorator
    - A endpoint.txt file in the repo
    Otherwise assigns a default one
    '''
    endpoint = 'http://dbpedia.org/sparql'

    # Decorator
    try:
        endpoint = get_metadata(rq)['endpoint']
	app.logger.info("Decorator guessed endpoint: " + endpoint)
    except (TypeError, KeyError, ParseException):
	# File
	try:
	    endpoint_file_uri = ru + "endpoint.txt"
	    stream = urllib2.urlopen(endpoint_file_uri)
	    endpoint = stream.read().strip()
 	    app.logger.debug("File guessed endpoint: " + endpoint)
	except:
	    # Default
            app.logger.warning("No endpoint specified, using default ({})".format(endpoint))

    return endpoint


def get_parameters(rq, endpoint):
    """
        ?_name The variable specifies the API mandatory parameter name. The value is incorporated in the query as plain literal.
        ?__name The parameter name is optional.
        ?_name_iri The variable is substituted with the parameter value as a IRI (also: number or literal).
        ?_name_en The parameter value is considered as literal with the language 'en' (e.g., en,it,es, etc.).
        ?_name_integer The parameter value is considered as literal and the XSD datatype 'integer' is added during substitution.
        ?_name_prefix_datatype The parameter value is considered as literal and the datatype 'prefix:datatype' is added during substitution. The prefix must be specified according to the SPARQL syntax.
    """

    variables = translateQuery(Query.parseString(rq, parseAll=True)).algebra['_vars']

    ## Aggregates
    internal_matcher = re.compile("__agg_\d+__")
    ## Basil-style variables
    variable_matcher = re.compile("(?P<required>[_]{1,2})(?P<name>[^_]+)_?(?P<type>[a-zA-Z0-9]+)?_?(?P<userdefined>[a-zA-Z0-9]+)?.*$")

    parameters = {}
    for v in variables:
        if internal_matcher.match(v):
            continue

        match = variable_matcher.match(v)
	# TODO: currently only one parameter per triple pattern is supported
        tpattern_matcher = re.compile(".*FROM\s+(?P<gnames>.*)\s+WHERE.*[\.\{][\n\t\s]*(?P<tpattern>.*\?" + re.escape(v) + ".*)\..*", flags=re.DOTALL)
        tp_match = tpattern_matcher.match(rq)
        if match :
            if tp_match:
                vtpattern = tp_match.group('tpattern')
                gnames = tp_match.group('gnames')
                app.logger.debug("Matched triple pattern with parameter")
                # app.logger.debug(vtpattern)
                # app.logger.debug(gnames)
                codes_subquery = re.sub("SELECT.*\{.*\}", "SELECT DISTINCT ?" + v + " FROM " + gnames + " WHERE { " + vtpattern + " . }", rq, flags=re.DOTALL)
                headers = {
                    'Accept' : 'application/json'
                }
                data = {
                    'query' : codes_subquery
                }
                data_encoded = urllib.urlencode(data)
                req = urllib2.Request(endpoint, data_encoded, headers)
                app.logger.debug("Sending code subquery request: " + req.get_full_url() + "?" + req.get_data())
                response = urllib2.urlopen(req)
                codes_json = json.loads(response.read())
                # app.logger.debug(codes_json)
                vcodes = []
                for code in codes_json['results']['bindings']:
                    vcodes.append(code.values()[0]["value"])
                # app.logger.debug(vcodes)
                
            vname = match.group('name')
            vrequired = True if match.group('required') == '_' else False
            vtype = 'literal'
            vlang = None
            vdatatype = None

            mtype = match.group('type')
            muserdefined = match.group('userdefined')

            if mtype in ['iri','number','literal']:
                vtype = mtype
            elif mtype:
                vtype = 'literal'

                if mtype:
                    if mtype in XSD_DATATYPES:
                        vdatatype = 'xsd:{}'.format(mtype)
                    elif len(mtype) == 2 :
                        vlang = mtype
                    elif muserdefined :
                        vdatatype = '{}:{}'.format(mtype, muserdefined)

            parameters[vname] = {
                'original': '?{}'.format(v),
                'required': vrequired,
                'name': vname,
                'enum': sorted(vcodes),
                'type': vtype,
                'datatype': vdatatype,
                'lang': vlang
            }

    return parameters


def get_metadata(rq):
    '''
    Returns the metadata 'exp' parsed from the raw query file 'rq'
    'exp' is one of: 'endpoint', 'tags', 'summary', 'request', 'pagination'
    '''
    if not rq:
        return None

    yaml_string = "\n".join([row.lstrip('#+') for row in rq.split('\n') if row.startswith('#+')])
    query_string = "\n".join([row for row in rq.split('\n') if not row.startswith('#+')])

    query_metadata = yaml.load(yaml_string)
    # If there is no YAML string
    if query_metadata == None:
        query_metadata = {}
    query_metadata['query'] = query_string

    try:
        parsed_query = translateQuery(Query.parseString(rq, parseAll=True))
        query_metadata['type'] = parsed_query.algebra.name
        if query_metadata['type'] == 'SelectQuery':
            query_metadata['variables'] = parsed_query.algebra['PV']
    except ParseException:
        app.logger.error("Could not parse query")
	app.logger.error(query_string)
        print traceback.print_exc()

    return query_metadata

def count_query_results(query, endpoint):
    '''
    Returns the total number of results that query 'query' will generate
    '''
    number_results_query, repl = re.subn("SELECT.*FROM", "SELECT COUNT (*) FROM", query)
    if not repl:
        number_results_query = re.sub("SELECT.*{", "SELECT COUNT(*) {", query)
    number_results_query = re.sub("GROUP\s+BY\s+[\?\_\(\)a-zA-Z0-9]+", "", number_results_query)
    number_results_query = re.sub("ORDER\s+BY\s+[\?\_\(\)a-zA-Z0-9]+", "", number_results_query)
    number_results_query = re.sub("LIMIT\s+[0-9]+", "", number_results_query)
    number_results_query = re.sub("OFFSET\s+[0-9]+", "", number_results_query)

    app.logger.debug("Query for result count: " + number_results_query)

    # Preapre HTTP request
    headers = { 'Accept' : 'application/json' }
    data = { 'query' : number_results_query }

    data_encoded = urllib.urlencode(data)
    req = urllib2.Request(endpoint, data_encoded, headers)
    response = urllib2.urlopen(req)
    count_json = json.loads(response.read())
    count = int(count_json['results']['bindings'][0]['callret-0']['value'])
    app.logger.info("Paginated query has {} results in total".format(count))

    return count

def paginate_query(query, get_args):
    query_metadata = get_metadata(query)
    if 'pagination' not in query_metadata:
        return query
    
    results_per_page = query_metadata['pagination']    
    page = get_args.get('page', 1)

    app.logger.info("Paginating query for page {}, {} results per page".format(page, results_per_page))

    # If contains LIMIT or OFFSET, remove them
    app.logger.debug("Original query: " + query)
    no_limit_query = re.sub("((LIMIT|OFFSET)\s+[0-9]+)*", "", query)
    app.logger.debug("No limit query: " + no_limit_query)

    # Append LIMIT results_per_page OFFSET (page-1)*results_per_page
    paginated_query = no_limit_query + " LIMIT {} OFFSET {}".format(results_per_page, (int(page) - 1) * results_per_page)
    app.logger.debug("Paginated query: " + paginated_query)

    return paginated_query

def rewrite_query(query, get_args, endpoint):
    parameters = get_parameters(query, endpoint)

    app.logger.debug("Query parameters")
    app.logger.debug(parameters)
    for pname, p in parameters.items():
        # Get the parameter value from the GET request
        v = get_args.get(pname, None)
        # If the parameter has a value
        if v:
            # IRI
            if p['type'] == 'iri':
                query = query.replace(p['original'], "{}{}{}".format('<',v,'>'))
            # A number (without a datatype)
            elif p['type'] == 'number':
                query = query.replace(p['original'], v)
            # Literals
            elif p['type'] == 'literal':
                # If there is a language tag
                if p['lang']:
                    query = query.replace(p['original'], "\"{}\"@{}".format(v, p['lang']))
                elif p['datatype']:
                    query = query.replace(p['original'], "\"{}\"^^{}".format(v, p['datatype']))
                else:
                    query = query.replace(p['original'], "\"{}\"".format(v))

    app.logger.debug("Query rewritten as: " + query)
    return query

def is_cache_updated(repo_uri):
    if repo_uri not in cache:
        return False
    cache_date = cache[repo_uri]['date']
    stream = urllib2.urlopen(repo_uri)
    resp = json.load(stream)
    github_date = resp['pushed_at']
    return cache_date > github_date

date_handler = lambda obj: (
    obj.isoformat()
    if isinstance(obj, datetime.datetime)
    or isinstance(obj, datetime.date)
    else None
)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/<user>/<repo>/<query>', methods=['GET'])
@app.route('/<user>/<repo>/<query>.<content>', methods=['GET'])
def query(user, repo, query, content=None):
    app.logger.debug("Got request at /" + user + "/" + repo + "/" + query)
    app.logger.debug("Request accept header: " +request.headers["Accept"])
    raw_repo_uri = 'https://raw.githubusercontent.com/' + user + '/' + repo + '/master/'
    raw_query_uri = raw_repo_uri + query + '.rq'
    stream = urllib2.urlopen(raw_query_uri)
    raw_query = stream.read()

    endpoint = guess_endpoint_uri(raw_query, raw_repo_uri)
    app.logger.debug("Sending query to endpoint: " + endpoint)

    query_metadata = get_metadata(raw_query)
    pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""

    # Rewrite query using parameter values
    query = rewrite_query(raw_query, request.args, endpoint)

    # Rewrite query using pagination
    paginated_query = paginate_query(query, request.args)

    # Preapre HTTP request
    headers = { 'Accept' : request.headers['Accept'] }
    if content:
        headers = { 'Accept' : mimetypes[content] }
    data = { 'query' : paginated_query }

    data_encoded = urllib.urlencode(data)
    req = urllib2.Request(endpoint, data_encoded, headers)
    app.logger.debug("Sending request: " + req.get_full_url() + "?" + req.get_data())
    response = urllib2.urlopen(req)
    app.logger.debug('Response header from endpoint: ' + response.info().getheader('Content-Type'))

    resp = make_response(response.read())
    resp.headers['Content-Type'] = response.info().getheader('Content-Type')
    # If the query is paginated, set link HTTP headers
    if pagination:
        # Get number of total results
        count = count_query_results(query, endpoint)
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

@app.route('/<user>/<repo>/api-docs')
def api_docs(user, repo):
    return render_template('api-docs.html', user=user, repo=repo)


@app.route('/<user>/<repo>/spec')
def swagger_spec(user, repo):
    app.logger.info("Generating swagger spec for /" + user + "/" + repo)
    api_repo_uri = 'https://api.github.com/repos/' + user + '/' + repo
    # Check if we have an updated cached spec for this repo
    if is_cache_updated(api_repo_uri):
        app.logger.info("Reusing updated cache for this spec")
        return jsonify(cache[api_repo_uri]['spec'])
    stream = urllib2.urlopen(api_repo_uri)
    resp = json.load(stream)
    swag = {}
    swag['swagger'] = '2.0'
    swag['info'] = {'version': '1.0', 'title': resp['name'], 'contact': {'name': resp['owner']['login'], 'url': resp['owner']['html_url']}, 'license': {'name' : 'License', 'url': 'https://raw.githubusercontent.com/' + user + '/' + repo + '/master/LICENSE'}}
    swag['host'] = app.config['SERVER_NAME']
    swag['basePath'] = '/' + user + '/' + repo + '/'
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
            raw_repo_uri = 'https://raw.githubusercontent.com/' + user + '/' + repo + '/master/'
            raw_query_uri = raw_repo_uri + c['name']
            stream = urllib2.urlopen(raw_query_uri)
            resp = stream.read()

            app.logger.info("Processing query " + raw_query_uri)

            try:
                query_metadata = get_metadata(resp)
            except Exception as e:
                app.logger.error("Could not parse query")
                app.logger.error(e)
                continue

            tags = query_metadata['tags'] if 'tags' in query_metadata else []
            app.logger.debug("Read query tags: " + ', '.join(tags))

            summary = query_metadata['summary'] if 'summary' in query_metadata else ""
            app.logger.debug("Read query summary: " + summary)

            description = query_metadata['description'] if 'description' in query_metadata else ""
            app.logger.debug("Read query description: " + description)

            method = query_metadata['method'].lower() if 'method' in query_metadata else "get"
            if method not in ['get', 'post', 'head', 'put', 'delete', 'options', 'connect']:
                method = "get"

            pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""
            app.logger.debug("Read query pagination: " + str(pagination))

            # endpoint = query_metadata['endpoint'] if 'endpoint' in query_metadata else ""
            endpoint = guess_endpoint_uri("", raw_repo_uri)
            app.logger.debug("Read query endpoint: " + endpoint)

            try:
                parameters = get_parameters(query_metadata['query'], endpoint)
            except Exception as e:
                print traceback.print_exc()

                app.logger.error("Could not parse parameters")
                continue

            app.logger.debug("Read request parameters")
            app.logger.debug(parameters)
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
                app.logger.warning("This is not a SelectQuery, don't really know what to do!")
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
    cache[api_repo_uri] = {'date' : json.dumps(datetime.datetime.now(), default=date_handler).split('\"')[1], 'spec' : swag}
    with open(CACHE_NAME, 'w') as cache_file:
        json.dump(cache, cache_file)
    app.logger.debug("Local cache updated")

    return jsonify(swag)

# DEPRECATED
# Do something on github pushes?
# @app.route('/sparql', methods = ['POST'])
# def sparql():
#     push = json.loads(request.data)
#     # One push may contain many commits
#     for c in push['commits']:
#         # We only look for .rq files
#         for a in c['added']:
#             if '.rq' in a:
#                 # New query added
#                 add_query(push['repository']['full_name'], a)
#         print c['added']
#         print c['removed']
#         print c['modified']

#         return 'foo'

if __name__ == '__main__':
    app.run(port=8088, debug=True)
