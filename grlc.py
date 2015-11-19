
#!/usr/bin/env python

from flask import Flask, request, jsonify, render_template
import urllib2
import json
from SPARQLWrapper import SPARQLWrapper, JSON
import StringIO
import logging
import re
import yaml
from rdflib.plugins.sparql.parser import Query
from rdflib.plugins.sparql.processor import translateQuery
import traceback
import cgi

XSD_DATATYPES = ["decimal", "float", "double", "integer", "positiveInteger", "negativeInteger", "nonPositiveInteger", "nonNegativeInteger", "long", "int", "short", "byte", "unsignedLong", "unsignedInt", "unsignedShort", "unsignedByte", "dateTime", "date", "gYearMonth", "gYear", "duration", "gMonthDay", "gDay", "gMonth", "string", "normalizedString", "token", "language", "NMTOKEN", "NMTOKENS", "Name", "NCName", "ID", "IDREFS", "ENTITY", "ENTITIES", "QName", "boolean", "hexBinary", "base64Binary", "anyURI", "notation"]


app = Flask(__name__)

def guess_endpoint_uri(rq, ru):
    '''
    Guesses the endpoint URI from (in this order):
    - An #+Endpoint decorator
    - A endpoint.txt file in the repo
    Otherwise assigns a default one
    '''
    endpoint = 'http://dbpedia.org/sparql'

    # Decorator
    endpoint = get_metadata(rq)['endpoint']
    if len(endpoint):
        app.logger.info("Decorator guessed endpoint: " + endpoint)
        return endpoint
    else:
        app.logger.warning("Couldn't guess endpoint from the query file")

    # Endpoint file in repo
    try:
        endpoint_file_uri = ru + "endpoint.txt"
        stream = urllib2.urlopen(endpoint_file_uri)
        endpoint = stream.read().strip()
        app.logger.info("File guessed endpoint: " + endpoint)
        return endpoint
    except IndexError:
        app.logger.warning("Couldn't guess endpoint from endpoint file")
        pass

    app.logger.warning("Using default endpoint " + endpoint)
    return endpoint


def get_parameters(rq):
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
        if match :
            vname = match.group('name')
            vrequired = True if match.group('required') == '_' else False
            vtype = 'iri'
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
                        vdatatype = mtype
                    elif len(mtype) == 2 :
                        vlang = mtype
                    elif muserdefined :
                        vdatatype = '{}:{}'.format(mtype, muserdefined)

            parameters[v] = {
                'original': '?{}'.format(v),
                'required': vrequired,
                'name': vname,
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
    query_metadata = yaml.load(yaml_string)

    parsed_query = translateQuery(Query.parseString(rq, parseAll=True))
    query_metadata['type'] = parsed_query.algebra.name

    if query_metadata['type'] == 'SelectQuery':
        query_metadata['variables'] = parsed_query.algebra['PV']

    return query_metadata

@app.route('/')
def hello():
    return 'This is grlc, it creates crappy apis out of your github stored SPARQL queries for the lulz'

@app.route('/<user>/<repo>/<query>')
def query(user, repo, query):
    app.logger.debug("Got request at /" + user + "/" + repo + "/" + query)
    app.logger.debug("Request accept header: " +request.headers["Accept"])
    raw_repo_uri = 'https://raw.githubusercontent.com/' + user + '/' + repo + '/master/'
    raw_query_uri = raw_repo_uri + query + '.rq'
    stream = urllib2.urlopen(raw_query_uri)
    raw_query = stream.read()

    endpoint = guess_endpoint_uri(raw_query, raw_repo_uri)
    app.logger.debug("Sending query to endpoint: " + endpoint)
    sparql = SPARQLWrapper(endpoint)
    app.logger.debug("Sending query: " + raw_query)
    sparql.setQuery(raw_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return jsonify(results)

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
    swag['info'] = {'version': '1.0', 'title': resp['name'], 'contact': {'name': resp['owner']['login'], 'url': resp['owner']['url']}, 'license': {'name' : 'licensename', 'url': 'licenseurl'}}
    swag['host'] = 'grlc.amp.ops.few.vu.nl'
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

            try :
                query_metadata = get_metadata(resp)
            except Exception as e:
                print resp

                app.logger.error("Could not parse query")
                continue



            tags = query_metadata['tags'] if 'tags' in query_metadata else []
            app.logger.debug("Read query tags: " + ', '.join(tags))

            summary = query_metadata['summary'] if 'summary' in query_metadata else ""
            app.logger.debug("Read query summary: " + summary)

            endpoint = query_metadata['endpoint'] if 'endpoint' in query_metadata else ""
            app.logger.debug("Read query endpoint: " + endpoint)

            try :
                parameters = get_parameters(resp)
            except Exception as e:
                print e
                app.logger.error("Could not parse parameters")
                continue

            app.logger.debug("Read parameters")
            app.logger.debug(parameters)
            # TODO: do something intelligent with the parameters!

            swag['paths'][call_name] = {}
            swag['paths'][call_name]["get"] = {"tags" : tags,
                                               "summary" : summary,
                                               "produces" : ["application/json", "text/csv"],
                                               "responses": {
                                                   "200" : {
                                                       "description" : "pet response",
                                                       "schema" : {
                                                           "type" : "object",
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
