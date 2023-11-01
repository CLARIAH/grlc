#!/usr/bin/env python

# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

# gquery.py: functions that deal with / transform SPARQL queries in grlc

import yaml
import json
from rdflib.plugins.sparql.parser import Query, UpdateUnit
from rdflib.plugins.sparql.processor import translateQuery
from flask import request, has_request_context
from pyparsing import ParseException
from pprint import pformat
import traceback
import re
import requests
import SPARQLTransformer

# grlc modules
import grlc.static as static
import grlc.glogging as glogging


glogger = glogging.getGrlcLogger(__name__)

XSD_PREFIX = "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>"


def guess_endpoint_uri(rq, loader):
    """
    Guesses the endpoint URI from (in this order):
    - An endpoint parameter in URL
    - An #+endpoint decorator
    - A endpoint.txt file in the repo
    Otherwise assigns a default one
    """
    auth = (static.DEFAULT_ENDPOINT_USER, static.DEFAULT_ENDPOINT_PASSWORD)
    if auth == ("none", "none"):
        auth = None

    if has_request_context() and "endpoint" in request.args:
        endpoint = request.args["endpoint"]
        glogger.debug("Endpoint provided in request: " + endpoint)
        return endpoint, auth

    # Decorator
    try:
        decorators = get_yaml_decorators(rq)
        endpoint = decorators["endpoint"]
        auth = None
        glogger.debug("Decorator guessed endpoint: " + endpoint)
    except (TypeError, KeyError):
        # File
        try:
            endpoint_content = loader.getEndpointText()
            endpoint = endpoint_content.strip().splitlines()[0]
            auth = None
            glogger.debug("File guessed endpoint: " + endpoint)
        # TODO: except all is really ugly
        except Exception:
            # Default
            endpoint = static.DEFAULT_ENDPOINT
            auth = (static.DEFAULT_ENDPOINT_USER, static.DEFAULT_ENDPOINT_PASSWORD)
            if auth == ("none", "none"):
                auth = None
            glogger.info("No endpoint specified, using default ({})".format(endpoint))

    return endpoint, auth


def count_query_results(query, endpoint):
    """
    Returns the total number of results that query 'query' will generate
    WARNING: This is too expensive just for providing a number of result pages
             Providing a dummy count for now
    """

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
    """Returns the first dictionary in dict_list which contains the given key"""
    for d in dict_list:
        if key in d:
            return d
    return None


def get_parameters(query, endpoint, query_metadata, auth=None):
    """
    ?_name The variable specifies the API mandatory parameter name. The value is incorporated in the query as plain literal.
    ?__name The parameter name is optional.
    ?_name_iri The variable is substituted with the parameter value as a IRI (also: number or literal).
    ?_name_en The parameter value is considered as literal with the language 'en' (e.g., en,it,es, etc.).
    ?_name_integer The parameter value is considered as literal and the XSD datatype 'integer' is added during substitution.
    ?_name_prefix_datatype The parameter value is considered as literal and the datatype 'prefix:datatype' is added during
        substitution. The prefix must be specified according to the SPARQL syntax.
    """
    # Basil-style variables
    re1 = r"\?"  # Start with a '?'
    re2 = "(?P<required>[_]{1,2})"  # ...followed by one (for required vars) or two (for optional vars) '_'
    re3 = "(?P<name>[a-zA-Z0-9]+)"  # ...then the name of the var
    re4 = "([_](?P<type>(iri)|(number)|(literal)|(integer)))?"  # ...optionally with a type (iri, number, literal, integer)
    re5 = "([_](?P<prefix>[a-zA-Z0-9]+)[_](?P<userdefined>[a-zA-Z0-9]+))?"  # ... OR a user defined type, with a prefix
    re6 = "([_](?P<lang>[a-zA-Z0-9]+))?"  # ...OR a language
    variable_matcher = re.compile(re1 + re2 + re3 + re4 + re5 + re6)

    parameters = {}
    for match in variable_matcher.finditer(query):
        p = {}
        vname = match.group("name")

        p["original"] = match.group(0)
        p["required"] = len(match.group("required")) == 1
        p["name"] = vname

        mtype = match.group("type")
        if mtype in ["number", "literal", "string"]:
            p["type"] = mtype
        elif mtype in ["iri"]:
            p["type"] = "string"
            p["format"] = "iri"
        else:
            p["type"] = "string"
            if mtype in static.XSD_DATATYPES:
                p["datatype"] = "xsd:{}".format(mtype)
            elif match.group("prefix") and match.group("userdefined"):
                p["datatype"] = "{}:{}".format(
                    match.group("prefix"), match.group("userdefined")
                )

        vcodes = get_enumeration(query, vname, endpoint, query_metadata, auth)
        if vcodes is not None:
            p["enum"] = sorted(vcodes)
        vdefault = get_defaults(query, vname, query_metadata)
        if vdefault is not None:
            p["default"] = vdefault

        if match.group("lang") is not None:
            p["lang"] = match.group("lang")

        parameters[vname] = p

    glogger.debug("Finished parsing the following parameters: {}".format(parameters))
    return parameters


def get_defaults(rq, v, metadata):
    """
    Returns the default value for a parameter or None
    """
    glogger.debug("Metadata with defaults: {}".format(metadata))
    if "defaults" not in metadata:
        return None
    defaultsDict = _getDictWithKey(v, metadata["defaults"])
    if defaultsDict:
        return defaultsDict[v]
    return None


def get_enumeration(rq, v, endpoint, metadata={}, auth=None):
    """
    Returns a list of enumerated values for variable 'v' in query 'rq'
    """
    # glogger.debug("Metadata before processing enums: {}".format(metadata))
    # We only fire the enum filling queries if indicated by the query metadata
    if "enumerate" not in metadata:
        return None
    enumDict = _getDictWithKey(v, metadata["enumerate"])
    if enumDict:
        return enumDict[v]
    if v in metadata["enumerate"]:
        return get_enumeration_sparql(rq, v, endpoint, auth)
    return None


def get_enumeration_sparql(rq, v, endpoint, auth=None):
    """
    Returns a list of enumerated values for variable 'v' in query 'rq'
    """
    glogger.debug("Retrieving enumeration for variable {}".format(v))
    vcodes = []

    # WHERE is optional too!!
    tpattern_matcher = re.compile(
        r".*?(FROM\s*(?P<gnames>\<.*\>+))?\s*(WHERE\s*)?\{(?P<tpattern>.*)\}.*",
        flags=re.DOTALL,
    )

    glogger.debug(rq)
    tp_match = tpattern_matcher.match(rq)
    if tp_match:
        vtpattern = tp_match.group("tpattern")
        gnames = tp_match.group("gnames")
        glogger.debug("Detected graph names: {}".format(gnames))
        glogger.debug("Detected BGP: {}".format(vtpattern))
        glogger.debug("Matched triple pattern with parameter")
        if gnames:
            codes_subquery = re.sub(
                r"SELECT.*\{.*\}.*",
                r"SELECT DISTINCT ?"
                + v
                + r" FROM "
                + gnames
                + r" WHERE { "
                + vtpattern
                + r" }",
                rq,
                flags=re.DOTALL,
            )
        else:
            codes_subquery = re.sub(
                r"SELECT.*\{.*\}.*",
                r"SELECT DISTINCT ?" + v + r" WHERE { " + vtpattern + " }",
                rq,
                flags=re.DOTALL,
            )
        glogger.debug("Codes subquery: {}".format(codes_subquery))
        glogger.debug(endpoint)
        codes_json = requests.get(
            endpoint,
            params={"query": codes_subquery},
            headers={
                "Accept": static.mimetypes["json"],
                "Authorization": "token {}".format(static.SPARQL_ACCESS_TOKEN),
            },
            auth=auth,
        ).json()
        for code in codes_json["results"]["bindings"]:
            vcodes.append(list(code.values())[0]["value"])
    else:
        glogger.debug("No match between variable name and query.")

    return vcodes


def get_yaml_decorators(rq):
    """
    Returns the yaml decorator metadata only (this is needed by triple pattern fragments)
    """
    # glogger.debug('Guessing decorators for query {}'.format(rq))
    if not rq:
        return None

    yaml_string = ""
    query_string = ""
    if isinstance(rq, dict):  # json query (sparql transformer)
        if "grlc" in rq:
            yaml_string = rq["grlc"]
            query_string = rq
            query_metadata = yaml_string

    else:  # classic query
        yaml_string = "\n".join(
            [row.lstrip("#+") for row in rq.split("\n") if row.startswith("#+")]
        )
        query_string = "\n".join(
            [row for row in rq.split("\n") if not row.startswith("#+")]
        )

        try:  # Invalid YAMLs will produce empty metadata
            query_metadata = yaml.safe_load(yaml_string)
        except (yaml.parser.ParserError, yaml.scanner.ScannerError):
            try:
                query_metadata = json.loads(yaml_string)
            except json.JSONDecodeError:
                glogger.warning(
                    "Query decorators could not be parsed; check your YAML syntax"
                )

    # If there is no YAML string
    if query_metadata is None:
        query_metadata = {}
    query_metadata["query"] = query_string

    # glogger.debug("Parsed query decorators: {}".format(query_metadata))

    return query_metadata


def enable_custom_function_prefix(rq, prefix):
    """Add SPARQL prefixe header if the prefix is used in the given query."""
    if (
        " %s:" % prefix in rq
        or "(%s:" % prefix in rq
        and not "PREFIX %s:" % prefix in rq
    ):
        rq = "PREFIX %s: <:%s>\n" % (prefix, prefix) + rq
    return rq


def get_metadata(rq, endpoint):
    """
    Returns the metadata 'exp' parsed from the raw query file 'rq'
    'exp' is one of: 'endpoint', 'tags', 'summary', 'request', 'pagination', 'enumerate'
    """
    query_metadata = get_yaml_decorators(rq)
    query_metadata["type"] = "UNKNOWN"
    query_metadata["original_query"] = rq

    if isinstance(rq, dict):  # json query (sparql transformer)
        rq, proto, opt = SPARQLTransformer.pre_process(rq)
        rq = rq.strip()
        query_metadata["proto"] = proto
        query_metadata["opt"] = opt
        query_metadata["query"] = rq

    rq = enable_custom_function_prefix(rq, "bif")
    rq = enable_custom_function_prefix(rq, "sql")

    try:
        # THE PARSING
        # select, describe, construct, ask
        parsed_query = translateQuery(Query.parseString(rq, parseAll=True))
        query_metadata["type"] = parsed_query.algebra.name
        if query_metadata["type"] == "SelectQuery":
            # Projection variables
            query_metadata["variables"] = parsed_query.algebra["PV"]
            # Parameters
            query_metadata["parameters"] = get_parameters(rq, endpoint, query_metadata)
        elif query_metadata["type"] == "ConstructQuery":
            # Parameters
            query_metadata["parameters"] = get_parameters(rq, endpoint, query_metadata)
        else:
            glogger.warning(
                "Query type {} is currently unsupported and no metadata was parsed!".format(
                    query_metadata["type"]
                )
            )
    except ParseException as pe:
        glogger.warning(pe)
        glogger.warning(
            "Could not parse regular SELECT, CONSTRUCT, DESCRIBE or ASK query"
        )
        # glogger.warning(traceback.print_exc())

        # insert queries won't parse, so we regex
        # glogger.info("Trying to parse INSERT query")
        # if static.INSERT_PATTERN in rq:
        #     query_metadata['type'] = 'InsertQuery'
        #     query_metadata['parameters'] = [u'_g_iri']

        try:
            # update query
            glogger.debug("Trying to parse UPDATE query")
            parsed_query = UpdateUnit.parseString(rq, parseAll=True)
            glogger.debug(parsed_query)
            query_metadata["type"] = parsed_query[0]["request"][0].name
            if query_metadata["type"] == "InsertData":
                query_metadata["parameters"] = {
                    "g": {
                        "datatype": None,
                        "enum": [],
                        "lang": None,
                        "name": "g",
                        "original": "?_g_iri",
                        "required": True,
                        "type": "iri",
                    },
                    "data": {
                        "datatype": None,
                        "enum": [],
                        "lang": None,
                        "name": "data",
                        "original": "?_data",
                        "required": True,
                        "type": "literal",
                    },
                }

            glogger.debug("Update query parsed with {}".format(query_metadata["type"]))
            # if query_metadata['type'] == 'InsertData':
            #     query_metadata['variables'] = parsed_query.algebra['PV']
        except Exception as e:
            glogger.error("Could not parse query")
            glogger.error(query_metadata["query"])
            glogger.error(traceback.print_exc())
            raise Exception("could not parse query: {}".format(str(e)))

    glogger.debug("Finished parsing query of type {}".format(query_metadata["type"]))
    glogger.debug("All parsed query metadata (from decorators and content): ")
    glogger.debug(pformat(query_metadata, indent=32))

    return query_metadata


def paginate_query(query, results_per_page, get_args):
    """Modify the given query so that it can be paginated. The paginated query will
    split display a maximum of `results_per_page`."""
    page = get_args.get("page", 1)

    glogger.debug(
        "Paginating query for page {}, {} results per page".format(
            page, results_per_page
        )
    )

    # If contains LIMIT or OFFSET, remove them
    glogger.debug("Original query: " + query)
    no_limit_query = re.sub(r"((LIMIT|OFFSET)\s+[0-9]+)*", "", query)
    glogger.debug("No limit query: " + no_limit_query)

    # Append LIMIT results_per_page OFFSET (page-1)*results_per_page
    paginated_query = no_limit_query + " LIMIT {} OFFSET {}".format(
        results_per_page, (int(page) - 1) * results_per_page
    )
    glogger.debug("Paginated query: " + paginated_query)

    return paginated_query


def rewrite_query(query, parameters, get_args):
    """Rewrite query to replace query parameters for given values."""
    glogger.debug("Query parameters")
    glogger.debug(parameters)

    # Check that all required parameters are present
    requiredParams = set(
        k for k, v in parameters.items() if v["required"]
    )  # Set of required parameters
    providedParams = set(get_args.keys())
    glogger.debug(
        "Required parameters: {} Request args: {}".format(
            requiredParams, providedParams
        )
    )
    assert requiredParams.issubset(
        providedParams
    ), "Provided parameters do not cover the required parameters!"

    if isinstance(query, dict):  # json query (sparql transformer)
        query = rewrite_query_json(query, parameters, get_args)
    else:
        query = rewrite_query_standard(query, parameters, get_args)

    glogger.debug("Query rewritten as: " + query)

    return query


def rewrite_query_json(query, parameters, get_args):
    for pname, p in parameters.items():
        # Get the parameter value from the GET request
        v = get_args.get(pname, None)
        # If the parameter has a value
        if not v:
            continue

        if "$values" not in query:
            query["$values"] = {}
        values = query["$values"]

        if not p["original"] in values:
            values[p["original"]] = v
        elif isinstance(values[p["original"]], list):
            values[p["original"]].append(v)
        else:
            values[p["original"]] = [values[p["original"]], v]

    rq, proto, opt = SPARQLTransformer.pre_process(query)
    query = rq.strip()
    return query


def rewrite_query_standard(query, parameters, get_args):
    requireXSD = False
    for pname, p in parameters.items():
        # Get the parameter value from the GET request
        v = get_args.get(pname, None)
        # If the parameter has a value
        if not v:
            continue

        # Number (without a datatype)
        if p["type"] == "number":
            query = query.replace(p["original"], v)
        # Literal
        elif p["type"] == "literal" or p["type"] == "string":
            # If it's a iri
            if "format" in p and p["format"] == "iri":
                query = query.replace(p["original"], "{}{}{}".format("<", v, ">"))
            # If there is a language tag
            if "lang" in p and p["lang"]:
                query = query.replace(p["original"], '"{}"@{}'.format(v, p["lang"]))
            elif "datatype" in p and p["datatype"]:
                query = query.replace(
                    p["original"], '"{}"^^{}'.format(v, p["datatype"])
                )
                if "xsd" in p["datatype"]:
                    requireXSD = True
            else:
                query = query.replace(p["original"], '"{}"'.format(v))
    if requireXSD and XSD_PREFIX not in query:
        query = query.replace("SELECT", XSD_PREFIX + "\n\nSELECT")
    return query
