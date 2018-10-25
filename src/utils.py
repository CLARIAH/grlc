import static as static
import gquery as gquery
import pagination as pageUtils
import swagger as swagger
from prov import grlcPROV
from fileLoaders import GithubLoader, LocalLoader
from queryTypes import qType
from grlc import __version__ as grlc_version

import re
import requests
import logging
import traceback

from rdflib import Graph

glogger = logging.getLogger(__name__)

def turtleize(swag):
    '''
    Transforoms a JSON swag object into a text/turtle LDA equivalent representation
    '''
    swag_graph = Graph()

    return swag_graph.serialize(format='turtle')

def getLoader(user, repo, sha=None, prov=None):
    if user is None and repo is None:
        loader = LocalLoader()
    else:
        loader = GithubLoader(user, repo, sha, prov)
    return loader

def build_spec(user, repo, sha=None, prov=None, extraMetadata=[]):
    '''
    Build grlc specification for the given github user / repo
    '''
    loader = getLoader(user, repo, sha=sha, prov=prov)

    files = loader.fetchFiles()
    raw_repo_uri = loader.getRawRepoUri()

    # Fetch all .rq files
    items = []

    for c in files:
        glogger.debug('>>>>>>>>>>>>>>>>>>>>>>>>>c_name: {}'.format(c['name']))
        if ".rq" in c['name'] or ".tpf" in c['name'] or ".sparql" in c['name']:
            call_name = c['name'].split('.')[0]

            # Retrieve extra metadata from the query decorators
            query_text = loader.getTextFor(c)

            item = None
            if ".rq" in c['name'] or ".sparql" in c['name']:
                glogger.debug("===================================================================")
                glogger.debug("Processing SPARQL query: {}".format(c['name']))
                glogger.debug("===================================================================")
                item = process_sparql_query_text(query_text, loader, call_name, extraMetadata)
            elif ".tpf" in c['name']:
                glogger.debug("===================================================================")
                glogger.debug("Processing TPF query: {}".format(c['name']))
                glogger.debug("===================================================================")
                item = process_tpf_query_text(query_text, raw_repo_uri, call_name, extraMetadata)
            else:
                glogger.info("Ignoring unsupported source call name: {}".format(c['name']))
            if item:
                items.append(item)
    return items

def process_tpf_query_text(query_text, raw_repo_uri, call_name, extraMetadata):
    query_metadata = gquery.get_yaml_decorators(query_text)

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

    endpoint = query_metadata['endpoint'] if 'endpoint' in query_metadata else ""
    glogger.debug("Read query endpoint: " + endpoint)

    # If this query allows pagination, add page number as parameter
    params = []
    if pagination:
        params.append(pageUtils.getSwaggerPaginationDef(pagination))

    item = {
        'call_name': call_name,
        'method': method,
        'tags': tags,
        'summary': summary,
        'description': description,
        'params': params,
        'query': query_metadata['query']
    }

    for extraField in extraMetadata:
        if extraField in query_metadata:
            item[extraField] = query_metadata[extraField]

    return item

def process_sparql_query_text(query_text, loader, call_name, extraMetadata):
    # We get the endpoint name first, since some query metadata fields (eg enums) require it

    endpoint, auth = gquery.guess_endpoint_uri(query_text, loader)
    glogger.debug("Read query endpoint: {}".format(endpoint))

    try:
        query_metadata = gquery.get_metadata(query_text, endpoint)
    except Exception:
        raw_repo_uri = loader.getRawRepoUri()
        raw_query_uri = raw_repo_uri + ' / ' + call_name
        glogger.error("Could not parse query at {}".format(raw_query_uri))
        glogger.error(traceback.print_exc())
        return None

    tags = query_metadata['tags'] if 'tags' in query_metadata else []

    summary = query_metadata['summary'] if 'summary' in query_metadata else ""

    description = query_metadata['description'] if 'description' in query_metadata else ""

    method = query_metadata['method'].lower() if 'method' in query_metadata else ""
    if method not in ['get', 'post', 'head', 'put', 'delete', 'options', 'connect']:
        method = ""

    pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""

    endpoint_in_url = query_metadata['endpoint_in_url'] if 'endpoint_in_url' in query_metadata else True

    # Processing of the parameters
    params = []

    # PV properties
    item_properties = {}

    # If this query allows pagination, add page number as parameter
    if pagination:
        params.append(pageUtils.getSwaggerPaginationDef(pagination))

    if query_metadata['type'] == 'SelectQuery' or query_metadata['type'] == 'ConstructQuery' or query_metadata['type'] == 'InsertData':
        # TODO: do something intelligent with the parameters!
        # As per #3, prefetching IRIs via SPARQL and filling enum
        parameters = query_metadata['parameters']

        for v, p in list(parameters.items()):
            param = {}
            param['name'] = p['name']
            param['type'] = p['type']
            param['required'] = p['required']
            param['in'] = "query"
            param['description'] = "A value of type {} that will substitute {} in the original query".format(p['type'], p['original'])
            if p['lang']:
                param['description'] = "A value of type {}@{} that will substitute {} in the original query".format(p['type'], p['lang'], p['original'])
            if p['format']:
                param['format'] = p['format']
                param['description'] = "A value of type {} ({}) that will substitute {} in the original query".format(p['type'], p['format'], p['original'])
            if p['enum']:
                param['enum'] = p['enum']

            params.append(param)

    if endpoint_in_url:
        endpoint_param = {}
        endpoint_param['name'] = "endpoint"
        endpoint_param['type'] = "string"
        endpoint_param['in'] = "query"
        endpoint_param['description'] = "Alternative endpoint for SPARQL query"
        endpoint_param['default'] = endpoint
        params.append(endpoint_param)

    if query_metadata['type'] == 'SelectQuery':
        # Fill in the spec for SELECT
        if not method:
            method = 'get'
        for pv in query_metadata['variables']:
            item_properties[pv] = {
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

    elif query_metadata['type'] == 'ConstructQuery':
        if not method:
            method = 'get'
    elif query_metadata['type'] == 'UNKNOWN':
        glogger.warning("grlc could not parse this query; assuming a plain, non-parametric SELECT in the API spec")
        if not method:
            method = 'get'
    else:
        # TODO: process all other kinds of queries
        glogger.warning("Query of type {} is currently unsupported! Skipping".format(query_metadata['type']))

    # Finally: main structure of the callname spec
    item = {
        'call_name': '/' + call_name,
        'method': method,
        'tags': tags,
        'summary': summary,
        'description': description,
        'params': params,
        'item_properties': None, # From projection variables, only SelectQuery
        'query': query_metadata['query']
    }

    for extraField in extraMetadata:
        if extraField in query_metadata:
            item[extraField] = query_metadata[extraField]

    return item

def build_swagger_spec(user, repo, sha, serverName):
    '''Build grlc specification for the given github user / repo in swagger format '''
    if user and repo:
        # Init provenance recording
        prov_g = grlcPROV(user, repo)
    else:
        prov_g = None

    swag = swagger.get_blank_spec()
    prev_commit, next_commit, info, basePath = \
        swagger.get_repo_info(user, repo, sha, prov_g)
    swag['host'] = serverName
    swag['prev_commit'] = prev_commit
    swag['next_commit'] = next_commit
    swag['info'] = info
    swag['basePath'] = basePath

    spec = build_spec(user, repo, sha, prov_g)
    for item in spec:
        swag['paths'][item['call_name']] = swagger.get_path_for_item(item)

    if prov_g:
        prov_g.end_prov_graph()
        swag['prov'] = prov_g.serialize(format='turtle')
    return swag

def dispatch_query(user, repo, query_name, sha, content, requestArgs, acceptHeader, requestUrl, formData):
    loader = getLoader(user, repo, sha=sha, prov=None)
    query, q_type = loader.getTextForName(query_name)

    # Call name implemented with SPARQL query
    if q_type == qType['SPARQL']:
        resp, status, headers = dispatchSPARQLQuery(query, loader, requestArgs, acceptHeader, content, formData, requestUrl)
        return resp, status, headers
    # Call name implemented with TPF query
    elif q_type == qType['TPF']:
        response, headers = dispatchTPFQuery(query, loader, acceptHeader, content)
        return response, 200, headers
    else:
        return "Couldn't find a SPARQL, RDF dump, or TPF query with the requested name", 404, {}

def dispatchSPARQLQuery(raw_sparql_query, loader, requestArgs, acceptHeader, content, formData, requestUrl):
    endpoint, auth = gquery.guess_endpoint_uri(raw_sparql_query, loader)
    if endpoint=='':
        return 'No SPARQL endpoint indicated', 407, {}

    glogger.debug("=====================================================")
    glogger.debug("Sending query to SPARQL endpoint: {}".format(endpoint))
    glogger.debug("=====================================================")

    query_metadata = gquery.get_metadata(raw_sparql_query, endpoint)

    pagination = query_metadata['pagination'] if 'pagination' in query_metadata else ""

    rewritten_query = query_metadata['query']

    # Rewrite query using parameter values
    if query_metadata['type'] == 'SelectQuery' or query_metadata['type'] == 'ConstructQuery':
        rewritten_query = gquery.rewrite_query(query_metadata['query'], query_metadata['parameters'], requestArgs)

    # Rewrite query using pagination
    if query_metadata['type'] == 'SelectQuery' and 'pagination' in query_metadata:
        rewritten_query = gquery.paginate_query(rewritten_query, query_metadata['pagination'], requestArgs)

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

        return resp_string, 200, {}

    headers = {
    }
    # Check for INSERT/POST
    if query_metadata['type'] == 'InsertData':
        glogger.debug("Processing INSERT query")
        # Rewrite INSERT
        rewritten_query = rewritten_query.replace("?_g_iri", "{}".format(formData.get('g')))
        rewritten_query = rewritten_query.replace("<s> <p> <o>", formData.get('data'))
        glogger.debug("INSERT query rewritten as {}".format(rewritten_query))

        # Prepare HTTP POST request
        reqHeaders = { 'Accept' : acceptHeader, 'Content-Type' : 'application/sparql-update' }
        response = requests.post(endpoint, data=rewritten_query, headers=reqHeaders, auth=auth)
        glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

        # Response headers
        resp = response.text
        headers['Content-Type'] = response.headers['Content-Type']

    # If there's no mime type, the endpoint is an actual SPARQL endpoint
    else:
        # requestedMimeType = static.mimetypes[content] if content else acceptHeader
        # result, contentType = sparql.getResponseText(endpoint, query, requestedMimeType)
        reqHeaders = { 'Accept' : acceptHeader }
        if content:
            reqHeaders = { 'Accept' : static.mimetypes[content]}
        data = { 'query' : rewritten_query }

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
        headerLink =  pageUtils.buildPaginationHeader(count, pagination, pageArg, requestUrl)
        headers['Link'] = headerLink

    headers['Server'] = 'grlc/' + grlc_version
    return resp, 200, headers

def dispatchTPFQuery(raw_tpf_query, loader, acceptHeader, content):
    endpoint, auth = gquery.guess_endpoint_uri(raw_tpf_query, loader)
    glogger.debug("=====================================================")
    glogger.debug("Sending query to TPF endpoint: {}".format(endpoint))
    glogger.debug("=====================================================")

    # TODO: pagination for TPF

    # Preapre HTTP request
    reqHeaders = { 'Accept' : acceptHeader , 'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}
    if content:
        reqHeaders = { 'Accept' : static.mimetypes[content] , 'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}
    tpf_list = re.split('\n|=', raw_tpf_query)
    subject = tpf_list[tpf_list.index('subject') + 1]
    predicate = tpf_list[tpf_list.index('predicate') + 1]
    object = tpf_list[tpf_list.index('object') + 1]
    data = { 'subject' : subject, 'predicate' : predicate, 'object' : object}

    response = requests.get(endpoint, params=data, headers=reqHeaders, auth=auth)
    glogger.debug('Response header from endpoint: ' + response.headers['Content-Type'])

    # Response headers
    resp = response.text
    headers = {}
    headers['Content-Type'] = response.headers['Content-Type']
    headers['Server'] = 'grlc/' + grlc_version
    return resp, 200, headers
