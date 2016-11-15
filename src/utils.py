import static
import requests
import gquery
import traceback
import cgi

import logging

glogger = logging.getLogger(__name__)

def build_spec(user, repo, default=False, extraMetadata=[]):
    '''
    Build grlc specification for the given github user / repo
    default: guess an API instead of reading it from remote .rq files
    '''
    api_repo_uri = static.GITHUB_API_BASE_URL + user + '/' + repo
    api_repo_content_uri = api_repo_uri + '/contents'
    raw_repo_uri = static.GITHUB_RAW_BASE_URL + user + '/' + repo + '/master/'

    resp = requests.get(api_repo_content_uri).json()
    # Fetch all .rq files
    items = []

    # default API
    if default:
        endpoint = gquery.guess_endpoint_uri("", raw_repo_uri)
        glogger.info("Building default API for endpoint {}".format(endpoint))

        types_json = requests.get(endpoint, params={'query': static.SPARQL_TYPES}, headers={'Accept': 'application/json'}).json()
        for entity_type in types_json['results']['bindings']:
            # Each of these is an entity type in the endpoint
            entity_type_uri = entity_type['type']['value']
            entity_type_name = entity_type_uri.split('/')[-1].split('#')[-1]
            glogger.debug('Processing API endpoints for entity type {}'.format(entity_type_name))

            item = {
                'call_name': entity_type_name,
                'method': 'GET',
                'tags': entity_type_name,
                'summary': 'A list of all instances of type {}'.format(entity_type_uri),
                'description': 'description',
                'params': None,
                'item_properties': None,
                'query': 'query'
            }
            items.append(item)
    # SPARQL-custom API
    else:
        for c in resp:
            if ".rq" in c['name']:
                call_name = c['name'].split('.')[0]
                # Retrieve extra metadata from the query decorators
                raw_query_uri = raw_repo_uri + c['name']
                resp = requests.get(raw_query_uri).text

                glogger.info("Processing query " + raw_query_uri)
                item = process_query_text(resp, raw_query_uri, raw_repo_uri, call_name, extraMetadata)
                if item:
                    items.append(item)

    return items

def process_query_text(resp, raw_query_uri, raw_repo_uri, call_name, extraMetadata):
    try:
        query_metadata = gquery.get_metadata(resp)
    except Exception as e:
        glogger.error("Could not parse query at {}".format(raw_query_uri))
        glogger.error(e)
        return None

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
        headers = query_metadata['headers'] if 'headers' in query_metadata else None
        parameters = gquery.get_parameters(query_metadata['query'], endpoint, headers=headers)
    except Exception as e:
        print traceback.print_exc()
        glogger.error("Could not parse parameters of query {}".format(raw_query_uri))
        return None

    glogger.debug("Read request parameters")
    glogger.debug(parameters)
    # TODO: do something intelligent with the parameters!
    # As per #3, prefetching IRIs via SPARQL and filling enum

    params = []
    for v, p in parameters.items():
        param = {}
        param['name'] = p['name']
        param['type'] = p['type']
        param['required'] = p['required']
        param['in'] = "query"
        param['description'] = "A value of type {} that will substitute {} in the original query".format(p['type'], p['original'])
        if p['enum']:
            param['enum'] = p['enum']

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
    item = {
        'call_name': call_name,
        'method': method,
        'tags': tags,
        'summary': summary,
        'description': description,
        'params': params,
        'item_properties': item_properties,
        'query': query_metadata['query']
    }
    for extraField in extraMetadata:
        if extraField in query_metadata:
            item[extraField] = query_metadata[extraField]

    return item

def build_swagger_spec(user, repo, serverName, default=False):
    '''Build GRLC specification for the given github user / repo in swagger format '''
    api_repo_uri = static.GITHUB_API_BASE_URL + user + '/' + repo
    # Check if we have an updated cached spec for this repo
    # if cache.is_cache_updated(cache_obj, api_repo_uri):
    #     glogger.info("Reusing updated cache for this spec")
    #     return jsonify(cache_obj[api_repo_uri]['spec'])
    resp = requests.get(api_repo_uri).json()

    swag = {}
    swag['swagger'] = '2.0'
    swag['info'] = {
        'version': '1.0',
        'title': resp['name'],
        'contact': {
            'name': resp['owner']['login'],
            'url': resp['owner']['html_url']
        },
        'license': {
            'name' : 'License',
            'url': static.GITHUB_RAW_BASE_URL + user + '/' + repo + '/master/LICENSE'
        }
    }
    swag['host'] = serverName
    swag['basePath'] = '/api/' + user + '/' + repo + '/'
    swag['schemes'] = ['http']
    swag['paths'] = {}

    spec = build_spec(user, repo, default)
    # glogger.debug("Current internal spec data structure")
    # glogger.debug(spec)
    for item in spec:
        swag['paths'][item['call_name']] = {}
        swag['paths'][item['call_name']][item['method']] = {
            "tags" : item['tags'],
            "summary" : item['summary'],
            "description" : item['description'] + "\n<pre>\n{}\n</pre>".format(cgi.escape(item['query'])),
            "produces" : ["text/csv", "application/json", "text/html"],
            "parameters": item['params'],
            "responses": {
                "200" : {
                    "description" : "SPARQL query response",
                    "schema" : {
                        "type" : "array",
                        "items": {
                            "type": "object",
                            "properties": item['item_properties']
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
    return swag
