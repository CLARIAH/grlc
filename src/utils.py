import grlc.static as static
import grlc.gquery as gquery
import grlc.pagination as pageUtils
import grlc.swagger as swagger
from grlc.prov import grlcPROV
from grlc.fileLoaders import GithubLoader, LocalLoader, ParamLoader
from grlc.queryTypes import qType
from grlc.projection import project
from grlc import __version__ as grlc_version

import re
import requests
import json

from rdflib import Graph

import SPARQLTransformer

import grlc.glogging as glogging

glogger = glogging.getGrlcLogger(__name__)

def getLoader(user, repo, subdir=None, query_urls=[], sha=None, prov=None):
    """Build a fileLoader (LocalLoader, GithubLoader, ParamLoader) for the given parameters."""
    if user is None and repo is None and not query_urls:
        loader = LocalLoader()
    elif query_urls:
        loader = ParamLoader(query_urls)
    else:
        loader = GithubLoader(user, repo, subdir, sha, prov)
    return loader


def build_spec(user, repo, subdir=None, sha=None, prov=None, extraMetadata=[]):
    glogger.warning("grlc.utils.build_spec is deprecated and will " \
                    "be removed in the future. Use grlc.swagger.build_spec instead.")
    return swagger.build_spec(user, repo, subdir, sha, prov, extraMetadata)


def build_swagger_spec(user, repo, subdir, query_urls, sha, serverName):
    """Build grlc specification for the given github user / repo in swagger format """
    if user and repo:
        # Init provenance recording
        prov_g = grlcPROV(user, repo)
    else:
        prov_g = None

    swag = swagger.get_blank_spec()
    swag['host'] = serverName

    try:
        loader = getLoader(user, repo, subdir, query_urls, sha, prov_g)
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
    if subdir:
        swag['basePath'] = basePath + subdir

    # TODO: can we pass loader to build_spec ? --> Ideally yes!
    spec = swagger.build_spec(user, repo, subdir, query_urls, sha, prov_g)
    for item in spec:
        swag['paths'][item['call_name']] = swagger.get_path_for_item(item)

    if prov_g:
        prov_g.end_prov_graph()
        swag['prov'] = prov_g.serialize(format='turtle')
    return swag


def dispatch_query(user, repo, query_name, subdir=None, sha=None, content=None, requestArgs={}, acceptHeader='application/json',
                   requestUrl='http://', formData={}):
    loader = getLoader(user, repo, subdir, sha=sha, prov=None)
    query, q_type = loader.getTextForName(query_name)

    # Call name implemented with SPARQL query
    if q_type == qType['SPARQL'] or q_type == qType['JSON']:
        resp, status, headers = dispatchSPARQLQuery(query, loader, requestArgs, acceptHeader, content, formData,
                                                    requestUrl)

        if acceptHeader == 'application/json':
            projection = loader.getProjectionForQueryName(query_name)
            if projection:
                dataIn = json.loads(resp)
                dataOut = project(dataIn, projection)
                resp = json.dumps(dataOut)

        return resp, status, headers
    # Call name implemented with TPF query
    elif q_type == qType['TPF']:
        resp, status, headers = dispatchTPFQuery(query, loader, acceptHeader, content)
        return resp, status, headers
    else:
        return "Couldn't find a SPARQL, RDF dump, or TPF query with the requested name", 404, {}


def dispatchSPARQLQuery(raw_sparql_query, loader, requestArgs, acceptHeader, content, formData, requestUrl):
    endpoint, auth = gquery.guess_endpoint_uri(raw_sparql_query, loader)
    if endpoint == '':
        return 'No SPARQL endpoint indicated', 407, {}

    glogger.debug("=====================================================")
    glogger.debug("Sending query to SPARQL endpoint: {}".format(endpoint))
    glogger.debug("=====================================================")

    query_metadata = gquery.get_metadata(raw_sparql_query, endpoint)

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
        response = requests.get(endpoint, params=data, headers=reqHeaders, auth=auth)
        glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

        # Response headers
        resp = response.text
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

    if 'transform' in query_metadata:  # sparql transformer
        rq = { 'proto': query_metadata['transform'] }
        _, _, opt = SPARQLTransformer.pre_process(rq)
        resp = SPARQLTransformer.post_process(json.loads(resp), query_metadata['transform'], opt)

    headers['Server'] = 'grlc/' + grlc_version
    return resp, 200, headers


def dispatchTPFQuery(raw_tpf_query, loader, acceptHeader, content):
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
