# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

import grlc.static as static
import grlc.gquery as gquery
import grlc.pagination as pageUtils
import grlc.swagger as swagger
from grlc.prov import grlcPROV
from grlc.fileLoaders import GithubLoader, LocalLoader, URLLoader, GitlabLoader
from grlc.queryTypes import qType
from grlc import __version__ as grlc_version

import re
import requests
import json

from rdflib import Graph

import SPARQLTransformer

import grlc.glogging as glogging

glogger = glogging.getGrlcLogger(__name__)

def getLoader(user, repo, subdir=None, spec_url=None, sha=None, prov=None, git_type=None, branch='main'):
    """Build a fileLoader (LocalLoader, GithubLoader, URLLoader) for the given parameters."""
    if user is None and repo is None and not spec_url:
        loader = LocalLoader()
    elif spec_url:
       loader = URLLoader(spec_url)
    else:
        if git_type == static.TYPE_GITHUB:
            glogger.debug("Building GithubLoader....")
            loader = GithubLoader(user, repo, subdir, sha, prov)
        else:
            glogger.debug("Building GitlabLoader....")
            loader = GitlabLoader(user, repo, subdir, sha, prov, branch)
    return loader


def build_spec(user, repo, subdir=None, sha=None, prov=None, extraMetadata=[]):
    """Build grlc specification for the given github user / repo.
    
    Deprecated."""
    glogger.warning("grlc.utils.build_spec is deprecated and will " \
                    "be removed in the future. Use grlc.swagger.build_spec instead.")
    items, _ = swagger.build_spec(user, repo, subdir, sha, prov, extraMetadata)
    return items


def build_swagger_spec(user, repo, subdir, spec_url, sha, serverName, git_type, branch='main'):
    """Build grlc specification for the given github user / repo in swagger format."""
    if user and repo:
        # Init provenance recording
        prov_g = grlcPROV(user, repo)
    else:
        prov_g = None

    swag = swagger.get_blank_spec()
    swag['host'] = serverName

    try:
        loader = getLoader(user, repo, subdir, spec_url, sha, prov_g, git_type, branch)
    except Exception as e:
        # If repo does not exits
        swag['info'] = {
            'title': 'ERROR!',
            'description': str(e)
        }
        swag['paths'] = {}
        return swag

    prev_commit, next_commit, info, basePath = \
        swagger.get_repo_info(loader, sha, prov_g)
    swag['prev_commit'] = prev_commit
    swag['next_commit'] = next_commit
    swag['info'] = info
    swag['basePath'] = basePath

    # TODO: can we pass loader to build_spec ? --> Ideally yes!
    spec, warnings = swagger.build_spec(user, repo, subdir, spec_url, sha, prov_g, [], git_type, branch)
    # Use items to build API paths
    for item in spec:
        swag['paths'][item['call_name']] = swagger.get_path_for_item(item)

     # TODO: Add bootstrap style to top level HTML
    # Without a better place to display warnings, we can make them part of the description.
    if 'description' not in swag['info'] or swag['info']['description'] is None:
        swag['info']['description'] = ''
    for warn in warnings:
        swag['info']['description'] += swagger.get_warning_div(warn)

    if prov_g:
        prov_g.end_prov_graph()
        swag['prov'] = prov_g.serialize(format='turtle')
    return swag


def dispatch_query(user, repo, query_name, subdir=None, spec_url=None, sha=None, 
        content=None, requestArgs={}, acceptHeader='application/json',
        requestUrl='http://', formData={}, method="POST", git_type=None, branch='main'):
    """Executes the specified SPARQL or TPF query."""
    loader = getLoader(user, repo, subdir, spec_url, sha=sha, prov=None, git_type=git_type, branch=branch)
    query, q_type = loader.getTextForName(query_name)

    # Call name implemented with SPARQL query
    if q_type == qType['SPARQL'] or q_type == qType['JSON']:
        resp, status, headers = dispatchSPARQLQuery(query, loader, requestArgs, acceptHeader, content, formData,
                                                    requestUrl, method)

        if acceptHeader == 'application/json':
            # TODO: transform JSON result if suitable
            pass

        return resp, status, headers
    # Call name implemented with TPF query
    elif q_type == qType['TPF']:
        resp, status, headers = dispatchTPFQuery(query, loader, acceptHeader, content)
        return resp, status, headers
    else:
        return "Couldn't find a SPARQL, RDF dump, or TPF query with the requested name", 404, {}


def dispatchSPARQLQuery(raw_sparql_query, loader, requestArgs, acceptHeader, content, 
        formData, requestUrl, method="GET"):
    """Executes the specified SPARQL query."""
    endpoint, auth = gquery.guess_endpoint_uri(raw_sparql_query, loader)
    if endpoint == '':
        return 'No SPARQL endpoint indicated', 407, {}

    glogger.debug("=====================================================")
    glogger.debug("Sending query to SPARQL endpoint: {}".format(endpoint))
    glogger.debug("=====================================================")

    try:
        query_metadata = gquery.get_metadata(raw_sparql_query, endpoint)
    except Exception as e:
        # extracting metadata
        return { 'error': str(e) }, 400, {}

    acceptHeader = 'application/json' if isinstance(raw_sparql_query, dict) else acceptHeader
    pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""

    rewritten_query = query_metadata['query']

    # Rewrite query using parameter values
    if query_metadata['type'] == 'SelectQuery' or query_metadata['type'] == 'ConstructQuery':
        rewritten_query = gquery.rewrite_query(query_metadata['original_query'], query_metadata['parameters'], requestArgs)

    # Rewrite query using pagination
    if query_metadata['type'] == 'SelectQuery' and 'pagination' in query_metadata:
        rewritten_query = gquery.paginate_query(rewritten_query, query_metadata['pagination'], requestArgs)

    resp = None
    headers = {}

    # If we have a mime field, we load the remote dump and query it locally
    if 'mime' in query_metadata and query_metadata['mime']:
        glogger.debug(
            "Detected {} MIME type, proceeding with locally loading remote dump".format(query_metadata['mime']))
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
        if 'application/json' in acceptHeader or (content and 'application/json' in static.mimetypes[content]):
            resp_string = results.serialize(format='json')
            glogger.debug("Results of SPARQL query against locally loaded dump: {}".format(resp_string))
        elif 'text/csv' in acceptHeader or (content and 'text/csv' in static.mimetypes[content]):
            resp_string = results.serialize(format='csv')
            glogger.debug("Results of SPARQL query against locally loaded dump: {}".format(resp_string))
        else:
            return 'Unacceptable requested format', 415, {}
        glogger.debug("Finished processing query against RDF dump, end of use case")
        del g

    # Check for INSERT/POST
    elif query_metadata['type'] == 'InsertData':
        glogger.debug("Processing INSERT query")
        if method != 'POST':
            glogger.debug('INSERT queries must use POST method')
            return { 'error': 'INSERT queries must use POST method' }, 400, headers

        # Rewrite INSERT
        rewritten_query = rewritten_query.replace("?_g_iri", "{}".format(formData.get('g')))
        rewritten_query = rewritten_query.replace("<s> <p> <o>", formData.get('data'))
        glogger.debug("INSERT query rewritten as {}".format(rewritten_query))

        # Prepare HTTP POST request
        reqHeaders = {'Accept': acceptHeader, 'Content-Type': 'application/sparql-update'}
        response = requests.post(endpoint, data=rewritten_query, headers=reqHeaders, auth=auth)
        glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

        # Response headers
        resp = response.text
        headers['Content-Type'] = response.headers['Content-Type']

    # If there's no mime type, the endpoint is an actual SPARQL endpoint
    else:
        reqHeaders = {'Accept': acceptHeader}
        if content:
            reqHeaders = {'Accept': static.mimetypes[content]}
        data = {'query': rewritten_query}

        glogger.debug('Sending HTTP request to SPARQL endpoint with params: {}'.format(data))
        glogger.debug('Sending HTTP request to SPARQL endpoint with headers: {}'.format(reqHeaders))
        glogger.debug('Sending HTTP request to SPARQL endpoint with auth: {}'.format(auth))
        try:
            response = requests.get(endpoint, params=data, headers=reqHeaders, auth=auth)
        except Exception as e:
            # Error contacting SPARQL endpoint
            glogger.debug('Exception encountered while connecting to SPARQL endpoint')
            return { 'error': str(e) }, 400, headers
        glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

        # Response headers
        resp = response.text

        glogger.debug('Got HTTP response from to SPARQL endpoint: {}'.format(resp))
        headers['Content-Type'] = response.headers['Content-Type']

    # If the query is paginated, set link HTTP headers
    if pagination:
        # Get number of total results
        count = gquery.count_query_results(rewritten_query, endpoint)
        pageArg = requestArgs.get('page', None)
        headerLink = pageUtils.buildPaginationHeader(count, pagination, pageArg, requestUrl)
        headers['Link'] = headerLink

    if 'proto' in query_metadata:  # sparql transformer
        resp = SPARQLTransformer.post_process(json.loads(resp), query_metadata['proto'], query_metadata['opt'])

    if 'transform' in query_metadata and acceptHeader == 'application/json':  # sparql transformer
        rq = { 'proto': query_metadata['transform'] }
        _, _, opt = SPARQLTransformer.pre_process(rq)
        resp = SPARQLTransformer.post_process(json.loads(resp), query_metadata['transform'], opt)

    headers['Server'] = 'grlc/' + grlc_version
    return resp, 200, headers


def dispatchTPFQuery(raw_tpf_query, loader, acceptHeader, content):
    """Executes the specified TPF query."""
    endpoint, auth = gquery.guess_endpoint_uri(raw_tpf_query, loader)
    glogger.debug("=====================================================")
    glogger.debug("Sending query to TPF endpoint: {}".format(endpoint))
    glogger.debug("=====================================================")

    # TODO: pagination for TPF

    # Preapre HTTP request
    reqHeaders = {'Accept': acceptHeader, 'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}
    if content:
        reqHeaders = {'Accept': static.mimetypes[content], 'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}
    tpf_list = re.split('\n|=', raw_tpf_query)
    subject = tpf_list[tpf_list.index('subject') + 1]
    predicate = tpf_list[tpf_list.index('predicate') + 1]
    object = tpf_list[tpf_list.index('object') + 1]
    data = {'subject': subject, 'predicate': predicate, 'object': object}

    response = requests.get(endpoint, params=data, headers=reqHeaders, auth=auth)
    glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

    # Response headers
    resp = response.text
    headers = {}
    headers['Content-Type'] = response.headers['Content-Type']
    headers['Server'] = 'grlc/' + grlc_version
    return resp, 200, headers
