#!/usr/bin/env python

# gquery.py: functions that deal with / transform SPARQL queries in grlc

import yaml
from rdflib.plugins.sparql.parser import Query
from rdflib.plugins.sparql.processor import translateQuery
from pyparsing import ParseException
import logging
import traceback
import re
import requests
import json

# grlc modules
import static

glogger = logging.getLogger(__name__)

def guess_endpoint_uri(rq, ru):
    '''
    Guesses the endpoint URI from (in this order):
    - An #+endpoint decorator
    - A endpoint.txt file in the repo
    Otherwise assigns a default one
    '''
    endpoint = static.DEFAULT_ENDPOINT

    # Decorator
    try:
        endpoint = get_metadata(rq)['endpoint']
        glogger.info("Decorator guessed endpoint: " + endpoint)
    except (TypeError, KeyError, ParseException):
	# File
    	try:
    	    endpoint_file_uri = ru + "endpoint.txt"
            endpoint = requests.get(endpoint_file_uri).text.strip()
     	    glogger.debug("File guessed endpoint: " + endpoint)
        # TODO: except all is really ugly
    	except:
    	    # Default
            glogger.warning("No endpoint specified, using default ({})".format(endpoint))

    return endpoint

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

def get_parameters(rq, endpoint, headers=None):
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
        tpattern_matcher = re.compile(".*(FROM\s+)?(?P<gnames>.*)\s+WHERE.*[\.\{][\n\t\s]*(?P<tpattern>.*\?" + re.escape(v) + ".*?\.).*", flags=re.DOTALL)
        tp_match = tpattern_matcher.match(rq)
        if match :
            vcodes = []
            if tp_match:
                vtpattern = tp_match.group('tpattern')
                gnames = tp_match.group('gnames')
                glogger.debug("Matched triple pattern with parameter")
                # glogger.debug(vtpattern)
                # glogger.debug(gnames)
                if gnames:
                    codes_subquery = re.sub("SELECT.*\{.*\}.*", "SELECT DISTINCT ?" + v + " FROM " + gnames + " WHERE { " + vtpattern + " }", rq, flags=re.DOTALL)
                else:
                    codes_subquery = re.sub("SELECT.*\{.*\}.*", "SELECT DISTINCT ?" + v + " WHERE { " + vtpattern + " }", rq, flags=re.DOTALL)
                glogger.debug("Codes subquery: {}".format(codes_subquery))
                headers = headers if headers else { 'Accept' : 'application/json' }
                data = {
                    'query' : codes_subquery
                }
                codes_json = requests.get(endpoint, params=data, headers=headers).json()
                # glogger.debug(codes_json)
                for code in codes_json['results']['bindings']:
                    vcodes.append(code.values()[0]["value"])
                # glogger.debug(vcodes)

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
        glogger.error("Could not parse query")
        glogger.error(query_string)
        print traceback.print_exc()

    return query_metadata

def paginate_query(query, get_args):
    query_metadata = get_metadata(query)
    if 'pagination' not in query_metadata:
        return query

    results_per_page = query_metadata['pagination']
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

def rewrite_query(query, get_args, endpoint):
    parameters = get_parameters(query, endpoint)

    glogger.debug("Query parameters")
    glogger.debug(parameters)
    requireXSD = False
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
                    if 'xsd' in p['datatype']:
                        requireXSD = True
                else:
                    query = query.replace(p['original'], "\"{}\"".format(v))

    xsdPrefix = 'PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>'
    if requireXSD and xsdPrefix not in query:
            query = query.replace('SELECT', xsdPrefix + '\n\nSELECT')
    glogger.debug("Query rewritten as: " + query)
    return query
