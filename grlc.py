#!/usr/bin/env python

from flask import Flask, request, jsonify, json, render_template
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

XSD_DATATYPES = ["decimal", "float", "double", "integer", "positiveInteger", "negativeInteger", "nonPositiveInteger", "nonNegativeInteger", "long", "int", "short", "byte", "unsignedLong", "unsignedInt", "unsignedShort", "unsignedByte", "dateTime", "date", "gYearMonth", "gYear", "duration", "gMonthDay", "gDay", "gMonth", "string", "normalizedString", "token", "language", "NMTOKEN", "NMTOKENS", "Name", "NCName", "ID", "IDREFS", "ENTITY", "ENTITIES", "QName", "boolean", "hexBinary", "base64Binary", "anyURI", "notation"]


app = Flask(__name__)

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
    except:
	# File
	try:
	    endpoint_file_uri = ru + "endpoint.txt"
	    stream = urllib2.urlopen(endpoint_file_uri)
	    endpoint = stream.read().strip()
 	    app.logger.info("File guessed endpoint: " + endpoint)
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
        app.logger.debug("Current variable")
        app.logger.debug(v)
        if internal_matcher.match(v):
            continue

        match = variable_matcher.match(v)
        tpattern_matcher = re.compile(".*FROM\s+(?P<gnames>.*)\s+WHERE.*\.[\n\t\s]*(?P<tpattern>.*\s+\?" + re.escape(v) + ").*", flags=re.DOTALL)
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
    'exp' is one of: 'endpoint', 'tags', 'summary'
    '''
    yaml_string = "\n".join([row.lstrip('#+') for row in rq.split('\n') if row.startswith('#+')])
    query_string = "\n".join([row for row in rq.split('\n') if not row.startswith('#+')])

    query_metadata = yaml.load(yaml_string)
    # If there is no YAML string
    if query_metadata == None:
        query_metadata = {}
    query_metadata['query'] = query_string

    try:
        parsed_query = translateQuery(Query.parseString(rq, parseAll=True))
    except ParseException:
        app.logger.error("Could not parse query")
	app.logger.error(query_string)
        print traceback.print_exc()
    query_metadata['type'] = parsed_query.algebra.name

    if query_metadata['type'] == 'SelectQuery':
        query_metadata['variables'] = parsed_query.algebra['PV']

    return query_metadata

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

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/<user>/<repo>/<query>', methods=['GET'])
def query(user, repo, query):
    app.logger.debug("Got request at /" + user + "/" + repo + "/" + query)
    app.logger.debug("Request accept header: " +request.headers["Accept"])
    raw_repo_uri = 'https://raw.githubusercontent.com/' + user + '/' + repo + '/master/'
    raw_query_uri = raw_repo_uri + query + '.rq'
    stream = urllib2.urlopen(raw_query_uri)
    raw_query = stream.read()

    endpoint = guess_endpoint_uri(raw_query, raw_repo_uri)
    app.logger.debug("Sending query to endpoint: " + endpoint)

    query = rewrite_query(raw_query, request.args, endpoint)

    # Preapre HTTP request
    headers = {
        'Accept' : request.headers['Accept']
    }
    data = {
	'query' : query
    }
    data_encoded = urllib.urlencode(data)
    req = urllib2.Request(endpoint, data_encoded, headers)
    app.logger.debug("Sending request: " + req.get_full_url() + "?" + req.get_data())
    response = urllib2.urlopen(req)

    return response.read()

@app.route('/<user>/<repo>/api-docs')
def api_docs(user, repo):
    return render_template('api-docs.html', user=user, repo=repo)

@app.route('/<user>/<repo>/spec')
def swagger_spec(user, repo):
    app.logger.debug("Generating swagger spec for /" + user + "/" + repo)
    api_repo_uri = 'https://api.github.com/repos/' + user + '/' + repo
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

            try:
                query_metadata = get_metadata(resp)
            except Exception as e:
                app.logger.error("Could not parse query " + raw_query_uri)
                app.logger.error(e)
                continue

            tags = query_metadata['tags'] if 'tags' in query_metadata else []
            app.logger.debug("Read query tags: " + ', '.join(tags))

            summary = query_metadata['summary'] if 'summary' in query_metadata else ""
            app.logger.debug("Read query summary: " + summary)

            description = query_metadata['description'] if 'description' in query_metadata else ""
            app.logger.debug("Read query description: " + description)

            # endpoint = query_metadata['endpoint'] if 'endpoint' in query_metadata else ""
            endpoint = guess_endpoint_uri("", raw_repo_uri)
            app.logger.debug("Read query endpoint: " + endpoint)

            try:
                parameters = get_parameters(query_metadata['query'], endpoint)
            except Exception as e:
                print traceback.print_exc()

                app.logger.error("Could not parse parameters")
                continue

            app.logger.debug("Read parameters")
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
            swag['paths'][call_name]["get"] = {"tags" : tags,
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
