#!/usr/bin/env python

# gquery.py: functions that deal with / transform SPARQL queries in grlc

import yaml
from rdflib.plugins.sparql.parser import Query, UpdateUnit
from rdflib.plugins.sparql.processor import translateQuery
from flask import request
from pyparsing import ParseException
import logging
from pprint import pformat
import traceback
import re
import requests

# grlc modules
import static as static

glogger = logging.getLogger(__name__)

def guess_endpoint_uri(rq, gh_repo):
    '''
    Guesses the endpoint URI from (in this order):
    - An endpoint parameter in URL
    - An #+endpoint decorator
    - A endpoint.txt file in the repo
    Otherwise assigns a default one
    '''
    endpoint = static.DEFAULT_ENDPOINT
    auth = (static.DEFAULT_ENDPOINT_USER, static.DEFAULT_ENDPOINT_PASSWORD)
    if auth == ('none','none'):
        auth = None

    if "endpoint" in request.args:
        endpoint = request.args['endpoint']
        glogger.info("Endpoint provided in request: " + endpoint)
        return endpoint, auth

    # Decorator
    try:
        decorators = get_yaml_decorators(rq)
        endpoint = decorators['endpoint']
        auth = None
        glogger.info("Decorator guessed endpoint: " + endpoint)
    except (TypeError, KeyError):
        # File
        try:
            endpoint_content = gh_repo.getTextFor({'download_url': 'endpoint.txt'})
            endpoint = endpoint_content.strip().splitlines()[0]
            auth = None
            glogger.debug("File guessed endpoint: " + endpoint)
        # TODO: except all is really ugly
        except:
            # Default
            endpoint = static.DEFAULT_ENDPOINT
            auth = (static.DEFAULT_ENDPOINT_USER, static.DEFAULT_ENDPOINT_PASSWORD)
            if auth == ('none','none'):
                auth = None
            glogger.warning("No endpoint specified, using default ({})".format(endpoint))

    return endpoint, auth

def count_query_results(query, endpoint):
    '''
    Returns the total number of results that query 'query' will generate
    WARNING: This is too expensive just for providing a number of result pages
             Providing a dummy count for now
    '''

    # number_results_query, repl = re.subn("SELECT.*FROM", "SELECT COUNT (*) FROM", query)
    # if not repl:
    #     number_results_query = re.sub("SELECT.*{", "SELECT COUNT(*) {", query)
    # number_results_query = re.sub("GROUP\s+BY\s+[\?\_\(\)a-zA-Z0-9]+", "", number_results_query)
    # number_results_query = re.sub("ORDER\s+BY\s+[\?\_\(\)a-zA-Z0-9]+", "", number_results_query)
    # number_results_query = re.sub("LIMIT\s+[0-9]+", "", number_results_query)
    # number_results_query = re.sub("OFFSET\s+[0-9]+", "", number_results_query)
    #
    # glogger.debug("Query for result count: " + number_results_query)
    #
    # # Preapre HTTP request
    # headers = { 'Accept' : 'application/json' }
    # data = { 'query' : number_results_query }
    # count_json = requests.get(endpoint, params=data, headers=headers).json()
    # count = int(count_json['results']['bindings'][0]['callret-0']['value'])
    # glogger.info("Paginated query has {} results in total".format(count))
    #
    # return count

    return 1000

def _getDictWithKey(key, dict_list):
    '''Return the first dictionary in dict_list which contains the given key'''
    for d in dict_list:
        if key in d:
            return d
    return None

def get_parameters(rq, variables, endpoint, query_metadata, auth=None):
    """
        ?_name The variable specifies the API mandatory parameter name. The value is incorporated in the query as plain literal.
        ?__name The parameter name is optional.
        ?_name_iri The variable is substituted with the parameter value as a IRI (also: number or literal).
        ?_name_en The parameter value is considered as literal with the language 'en' (e.g., en,it,es, etc.).
        ?_name_integer The parameter value is considered as literal and the XSD datatype 'integer' is added during substitution.
        ?_name_prefix_datatype The parameter value is considered as literal and the datatype 'prefix:datatype' is added during substitution. The prefix must be specified according to the SPARQL syntax.
    """

    # variables = translateQuery(Query.parseString(rq, parseAll=True)).algebra['_vars']

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
        if match :
            vname = match.group('name')
            vcodes = get_enumeration(rq, v, endpoint, query_metadata, auth)
            vrequired = True if match.group('required') == '_' else False
            vtype = 'string'
            vlang = None
            vdatatype = None
            vformat = None

            mtype = match.group('type')
            muserdefined = match.group('userdefined')

            if mtype in ['number','literal','string']:
                vtype = mtype
            if mtype in ['iri']: #TODO: proper form validation of input parameter uris
                vtype = 'string'
                vformat = 'iri'
            elif mtype:
                vtype = 'string'

                if mtype in static.XSD_DATATYPES:
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
                'lang': vlang,
                'format': vformat
            }

            glogger.info('Finished parsing the following parameters: {}'.format(parameters))

    return parameters

def get_enumeration(rq, v, endpoint, metadata={}, auth=None):
    '''
    Returns a list of enumerated values for variable 'v' in query 'rq'
    '''
    v = v.replace('_', '')

    # We only fire the enum filling queries if indicated by the query metadata
    if 'enumerate' not in metadata:
        return []
    enumDict = _getDictWithKey(v, metadata['enumerate'])
    if enumDict:
        return enumDict[v]
    if v in metadata['enumerate']:
        return get_enumeration_sparql(rq, v, endpoint, auth)
    return []

def get_enumeration_sparql(rq, v, endpoint, auth=None):
    '''
    Returns a list of enumerated values for variable 'v' in query 'rq'
    '''
    glogger.info('Retrieving enumeration for variable {}'.format(v))
    vcodes = []
    # tpattern_matcher = re.compile(".*(FROM\s+)?(?P<gnames>.*)\s+WHERE.*[\.\{][\n\t\s]*(?P<tpattern>.*\?" + re.escape(v) + ".*?\.).*", flags=re.DOTALL)
    # tpattern_matcher = re.compile(".*?((FROM\s*)(?P<gnames>(\<.*\>)+))?\s*WHERE\s*\{(?P<tpattern>.*)\}.*", flags=re.DOTALL)

    # WHERE is optional too!!
    tpattern_matcher = re.compile(".*?(FROM\s*(?P<gnames>\<.*\>+))?\s*(WHERE\s*)?\{(?P<tpattern>.*)\}.*", flags=re.DOTALL)

    glogger.debug(rq)
    tp_match = tpattern_matcher.match(rq)
    if tp_match:
        vtpattern = tp_match.group('tpattern')
        gnames = tp_match.group('gnames')
        glogger.debug("Detected graph names: {}".format(gnames))
        glogger.debug("Detected BGP: {}".format(vtpattern))
        glogger.debug("Matched triple pattern with parameter")
        if gnames:
            codes_subquery = re.sub("SELECT.*\{.*\}.*", "SELECT DISTINCT ?" + v + " FROM " + gnames + " WHERE { " + vtpattern + " }", rq, flags=re.DOTALL)
        else:
            codes_subquery = re.sub("SELECT.*\{.*\}.*", "SELECT DISTINCT ?" + v + " WHERE { " + vtpattern + " }", rq, flags=re.DOTALL)
        glogger.debug("Codes subquery: {}".format(codes_subquery))
        glogger.debug(endpoint)
        codes_json = requests.get(endpoint, params={'query' : codes_subquery}, headers={'Accept' : static.mimetypes['json'], 'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}, auth=auth).json()
        for code in codes_json['results']['bindings']:
            vcodes.append(list(code.values())[0]["value"])
    else:
        glogger.debug("No match between variable name and query.")

    return vcodes

def get_yaml_decorators(rq):
    '''
    Returns the yaml decorator metadata only (this is needed by triple pattern fragments)
    '''
    #glogger.debug('Guessing decorators for query {}'.format(rq))
    if not rq:
        return None

    yaml_string = "\n".join([row.lstrip('#+') for row in rq.split('\n') if row.startswith('#+')])
    query_string = "\n".join([row for row in rq.split('\n') if not row.startswith('#+')])

    query_metadata = None
    try: # Invalid YAMLs will produce empty metadata
        query_metadata = yaml.load(yaml_string)
    except yaml.scanner.ScannerError:
        glogger.warning("Query decorators could not be parsed; check your YAML syntax")
        pass

    # If there is no YAML string
    if query_metadata == None:
        query_metadata = {}
    query_metadata['query'] = query_string

    #glogger.debug("Parsed query decorators: {}".format(query_metadata))

    return query_metadata

def get_metadata(rq, endpoint):
    '''
    Returns the metadata 'exp' parsed from the raw query file 'rq'
    'exp' is one of: 'endpoint', 'tags', 'summary', 'request', 'pagination', 'enumerate'
    '''
    query_metadata = get_yaml_decorators(rq)
    query_metadata['type'] = 'UNKNOWN'

    try:
        # THE PARSING
        # select, describe, construct, ask
        parsed_query = translateQuery(Query.parseString(rq, parseAll=True))
        query_metadata['type'] = parsed_query.algebra.name
        if query_metadata['type'] == 'SelectQuery':
            # Projection variables
            query_metadata['variables'] = parsed_query.algebra['PV']
            # Parameters
            query_metadata['parameters'] = get_parameters(rq, parsed_query.algebra['_vars'], endpoint, query_metadata)
        elif query_metadata['type'] == 'ConstructQuery':
            # Parameters
            query_metadata['parameters'] = get_parameters(rq, parsed_query.algebra['_vars'], endpoint, query_metadata)
        else:
            glogger.warning("Query type {} is currently unsupported and no metadata was parsed!".format(query_metadata['type']))
    except ParseException:
        glogger.warning("Could not parse regular SELECT, CONSTRUCT, DESCRIBE or ASK query")
        # glogger.warning(traceback.print_exc())

        # insert queries won't parse, so we regex
        # glogger.info("Trying to parse INSERT query")
        # if static.INSERT_PATTERN in rq:
        #     query_metadata['type'] = 'InsertQuery'
        #     query_metadata['parameters'] = [u'_g_iri']

        try:
            # update query
            glogger.info("Trying to parse UPDATE query")
            parsed_query = UpdateUnit.parseString(rq, parseAll=True)
            glogger.info(parsed_query)
            query_metadata['type'] = parsed_query[0]['request'][0].name
            if query_metadata['type'] == 'InsertData':
                query_metadata['parameters'] = {'g': {'datatype': None, 'enum': [], 'lang': None, 'name': 'g', 'original': '?_g_iri', 'required': True, 'type': 'iri'},
                                                'data': {'datatype': None, 'enum': [], 'lang': None, 'name': 'data', 'original': '?_data', 'required': True, 'type': 'literal'}}

            glogger.info("Update query parsed with {}".format(query_metadata['type']))
            # if query_metadata['type'] == 'InsertData':
            #     query_metadata['variables'] = parsed_query.algebra['PV']
        except:
            glogger.error("Could not parse query")
            glogger.error(query_metadata['query'])
            glogger.error(traceback.print_exc())
            pass

    glogger.info("Finished parsing query of type {}".format(query_metadata['type']))
    glogger.info("All parsed query metadata (from decorators and content): ")
    glogger.info(pformat(query_metadata, indent=32))

    return query_metadata

def paginate_query(query, results_per_page, get_args):
    page = get_args.get('page', 1)

    glogger.info("Paginating query for page {}, {} results per page".format(page, results_per_page))

    # If contains LIMIT or OFFSET, remove them
    glogger.debug("Original query: " + query)
    no_limit_query = re.sub("((LIMIT|OFFSET)\s+[0-9]+)*", "", query)
    glogger.debug("No limit query: " + no_limit_query)

    # Append LIMIT results_per_page OFFSET (page-1)*results_per_page
    paginated_query = no_limit_query + " LIMIT {} OFFSET {}".format(results_per_page, (int(page) - 1) * results_per_page)
    glogger.debug("Paginated query: " + paginated_query)

    return paginated_query

def rewrite_query(query, parameters, get_args):
    glogger.debug("Query parameters")
    glogger.debug(parameters)
    requireXSD = False

    required_params = {}
    for k,v in parameters.iteritems():
        if parameters[k]['required']:
            required_params[k] = v
    requiredParams = set(required_params.keys())
    providedParams = set(get_args.keys())
    glogger.debug("Required parameters: {} Request args: {}".format(requiredParams, providedParams))
    assert requiredParams.issubset(providedParams), 'Provided parameters do not cover the required parameters!'

    for pname, p in list(parameters.items()):
        # Get the parameter value from the GET request
        v = get_args.get(pname, None)
        # If the parameter has a value
        if v:
            # IRI
            if p['type'] == 'iri': # TODO: never reached anymore, since iris are now type=string with format=iri
                query = query.replace(p['original'], "{}{}{}".format('<',v,'>'))
            # A number (without a datatype)
            elif p['type'] == 'number':
                query = query.replace(p['original'], v)
            # Literals
            elif p['type'] == 'literal' or p['type'] == 'string':
                # If it's a iri
                if p['format'] == 'iri':
                    query = query.replace(p['original'], "{}{}{}".format('<',v,'>'))
                # If there is a language tag
                if p['lang']:
                    query = query.replace(p['original'], "\"{}\"@{}".format(v, p['lang']))
                elif p['datatype']:
                    query = query.replace(p['original'], "\"{}\"^^{}".format(v, p['datatype']))
                    if 'xsd' in p['datatype']:
                        requireXSD = True
                else:
                    query = query.replace(p['original'], "\"{}\"".format(v))

    xsdPrefix = 'PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>'
    if requireXSD and xsdPrefix not in query:
            query = query.replace('SELECT', xsdPrefix + '\n\nSELECT')

    glogger.debug("Query rewritten as: " + query)

    return query
