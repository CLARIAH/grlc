import static
import requests
import gquery
import traceback
import cgi

def build_spec(user, repo, glogger):
    '''Build GRLC specification for the given github user / repo '''
    api_repo_uri = static.GITHUB_API_BASE_URL + user + '/' + repo

    api_repo_content_uri = api_repo_uri + '/contents'
    resp = requests.get(api_repo_content_uri).json()
    # Fetch all .rq files
    items = []
    for c in resp:
        if ".rq" in c['name']:
            call_name = c['name'].split('.')[0]
            # Retrieve extra metadata from the query decorators
            raw_repo_uri = static.GITHUB_RAW_BASE_URL + user + '/' + repo + '/master/'
            raw_query_uri = raw_repo_uri + c['name']
            resp = requests.get(raw_query_uri).text

            glogger.info("Processing query " + raw_query_uri)
            try:
                query_metadata = gquery.get_metadata(resp)
            except Exception as e:
                glogger.error("Could not parse query at {}".format(raw_query_uri))
                glogger.error(e)
                continue

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
                parameters = gquery.get_parameters(query_metadata['query'], endpoint)
            except Exception as e:
                print traceback.print_exc()

                glogger.error("Could not parse parameters of query {}".format(raw_query_uri))
                continue

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
            items.append(item)
    return items

def build_swagger_spec(user, repo, serverName, glogger):
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

    spec = build_spec(user, repo, glogger)
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
