# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

import json
import grlc.utils
import grlc.gquery as gquery
import grlc.pagination as pageUtils
from grlc.fileLoaders import GithubLoader, LocalLoader, URLLoader, GitlabLoader

import traceback
import grlc.glogging as glogging

glogger = glogging.getGrlcLogger(__name__)

def get_blank_spec():
    """Creates the base (blank) structure of swagger specification."""
    swag = {}
    swag['swagger'] = '2.0'
    swag['schemes'] = []  # 'http' or 'https' -- leave blank to make it dependent on how UI is loaded
    swag['paths'] = {}
    swag['definitions'] = {
        'Message': {'type': 'string'}
    }
    return swag


def get_repo_info(loader, sha, prov_g):
    """Generate swagger information from the repo being used."""
    user_repo = loader.getFullName()
    repo_title = loader.getRepoTitle()
    repo_desc = loader.getRepoDescription()
    contact_name = loader.getContactName()
    contact_url = loader.getContactUrl()
    commit_list = loader.getCommitList()
    licence_url = loader.getLicenceURL()    # This will be None if there is no license

    # Add the API URI as a used entity by the activity
    if prov_g:
        prov_g.add_used_entity(loader.getRepoURI())

    prev_commit = None
    next_commit = None
    version = sha if sha else commit_list[0]
    if commit_list.index(version) < len(commit_list) - 1:
        prev_commit = commit_list[commit_list.index(version) + 1]
    if commit_list.index(version) > 0:
        next_commit = commit_list[commit_list.index(version) - 1]

    info = {
        'version': version,
        'title': repo_title,
        'description': repo_desc,
        'contact': {
            'name': contact_name,
            'url': contact_url
        } 
    }
    if licence_url:
        info['license'] = {
            'name': 'License',
            'url': licence_url
        }

    if type(loader) is GithubLoader:
        basePath = '/api-git/' + user_repo + '/'
        basePath += ('subdir/' + loader.subdir + '/') if loader.subdir else ''
        basePath += ('commit/' + sha + '/') if sha else ''
    if type(loader) is GitlabLoader:
        basePath = '/api-gitlab/' + user_repo + '/query/' 
        basePath += ('branch/' + loader.branch + '/') if loader.branch else ''
        basePath += ('subdir/' + loader.subdir.strip('/') + '/') if loader.subdir else ''
        basePath += ('commit/' + sha + '/') if sha else ''
    elif type(loader) is LocalLoader:
        basePath = '/api-local/'
    elif type(loader) is URLLoader:
        basePath = '/api-url/'
    else:
        # TODO: raise error
        glogger.error('Cannot set basePath, loader type unkown')

    return prev_commit, next_commit, info, basePath


def get_path_for_item(item):
    """Builds the swagger definition for a specific path, based on 
    the given item."""
    query = item['original_query']
    if isinstance(query, dict):
        if 'grlc' in query:
            del query['grlc']
        query = "\n" + json.dumps(query, indent=2) + "\n"

    description = item['description']
    description += '\n\n```\n{}\n```'.format(query)
    description += '\n\nSPARQL transformation:\n```json\n{}```'.format(
        item['transform']) if 'transform' in item else ''

    item_path = {
        item['method']: {
            'tags': item['tags'],
            'summary': item['summary'],
            'description': description,
            'produces': ['text/csv', 'application/json', 'text/html'],
            'parameters': item['params'] if 'params' in item else None,
            'responses': {
                '200': {
                    'description': 'Query response',
                    'schema': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': item['item_properties'] if 'item_properties' in item else None
                        },
                    }
                },
                'default': {
                    'description': 'Unexpected error',
                    'schema': {
                        '$ref': '#/definitions/Message'
                    }
                }
            }
        }
    }
    return item_path


def build_spec(user, repo, subdir=None, query_url=None, sha=None, prov=None, extraMetadata=[], git_type=None, branch='main'):
    """Build grlc specification for the given github user / repo."""
    loader = grlc.utils.getLoader(user, repo, subdir, query_url, sha=sha, prov=prov, git_type=git_type, branch=branch)

    files = loader.fetchFiles()
    raw_repo_uri = loader.getRawRepoUri()

    # Fetch all .rq files
    items = []
    warnings = []

    allowed_ext = ["rq", "sparql", "json", "tpf"]
    for c in files:
        glogger.debug('>>>>>>>>>>>>>>>>>>>>>>>>>c_name: {}'.format(c['name']))
        extension = c['name'].split('.')[-1]
        if extension in allowed_ext or query_url: # parameter provided queries may not have extension
            call_name = c['name'].split('.')[0]

            # Retrieve extra metadata from the query decorators
            query_text = loader.getTextFor(c)

            item = None
            if extension == "json":
                query_text = json.loads(query_text)

            if extension in ["rq", "sparql", "json"] or query_url:
                glogger.debug("===================================================================")
                glogger.debug("Processing SPARQL query: {}".format(c['name']))
                glogger.debug("===================================================================")
                try:
                    item = process_sparql_query_text(query_text, loader, call_name, extraMetadata)
                except Exception as e:
                    warnings.append(str(e))
            elif "tpf" == extension:
                glogger.debug("===================================================================")
                glogger.debug("Processing TPF query: {}".format(c['name']))
                glogger.debug("===================================================================")
                item = process_tpf_query_text(query_text, raw_repo_uri, call_name, extraMetadata)
                # TODO: raise exceptions in process_tpf_query_text
            else:
                glogger.info("Ignoring unsupported source call name: {}".format(c['name']))

            if item:
                items.append(item)

    # Add a warning if no license is found
    if loader.getLicenceURL() is None:
        warnings.append("Queries behind this API do not have a license. You may not be allowed to use them.")

    return items, warnings


def process_tpf_query_text(query_text, raw_repo_uri, call_name, extraMetadata):
    """Generates a swagger specification item based on the given TPF query file."""
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

    item = packItem('/' + call_name, method, tags, summary, description, params, query_metadata, extraMetadata)

    return item


def process_sparql_query_text(query_text, loader, call_name, extraMetadata):
    """Generates a swagger specification item based on the given SPARQL query file."""
    # We get the endpoint name first, since some query metadata fields (eg enums) require it
    endpoint, _ = gquery.guess_endpoint_uri(query_text, loader)
    glogger.debug("Read query endpoint: {}".format(endpoint))

    try:
        query_metadata = gquery.get_metadata(query_text, endpoint)
    except Exception as e:
        raise Exception('Could not parse query {}: {}'.format(call_name, str(e)))

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

    if query_metadata['type'] in ['SelectQuery', 'ConstructQuery', 'InsertData']:
        # TODO: do something intelligent with the parameters!
        # As per #3, prefetching IRIs via SPARQL and filling enum
        parameters = query_metadata['parameters']

        for _, p in list(parameters.items()):
            param = {}
            param['name'] = p['name']
            param['type'] = p['type']
            param['required'] = p['required']
            param['in'] = "query"
            param['description'] = "A value of type {} that will substitute {} in the original query".format(
                    p['type'],  p['original'])
            if 'lang' in p:
                param['description'] = "A value of type {}@{} that will substitute {} in the original query".format(
                    p['type'], p['lang'], p['original'])
            if 'format' in p:
                param['format'] = p['format']
                param['description'] = "A value of type {} ({}) that will substitute {} in the original query".format(
                    p['type'], p['format'], p['original'])
            if 'enum' in p:
                param['enum'] = p['enum']
            if 'default' in p:
                param['default'] = p['default']

            params.append(param)

    if endpoint_in_url:
        endpoint_param = {}
        endpoint_param['name'] = "endpoint"
        endpoint_param['type'] = "string"
        endpoint_param['in'] = "query"
        endpoint_param['description'] = "Alternative endpoint for SPARQL query"
        endpoint_param['default'] = endpoint
        params.append(endpoint_param)

    # If this is a URL generated spec we need to force API calls with the specUrl parameter set
    if type(loader) is URLLoader:
        specUrl_param = {}
        specUrl_param['name'] = "specUrl"
        specUrl_param['type'] = "string"
        specUrl_param['in'] = "query"
        specUrl_param['description'] = "URL of the API specification"
        specUrl_param['default'] = loader.getRawRepoUri()
        params.append(specUrl_param)

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
    elif query_metadata['type'] == 'InsertData' or query_metadata['type'] == 'Modify': # UPDATE queries should map here
        if not method:
            method = 'post'
    elif query_metadata['type'] == 'UNKNOWN':
        glogger.warning("grlc could not parse this query; assuming a plain, non-parametric SELECT in the API spec")
        if not method:
            method = 'get'
    else:
        # TODO: process all other kinds of queries
        glogger.debug('Could not parse query {}: Query of type {} is currently unsupported'.format(call_name, query_metadata['type']))
        raise Exception('Could not parse query {}: Query of type {} is currently unsupported'.format(call_name, query_metadata['type']))

    # Finally: main structure of the callname spec
    item = packItem('/' + call_name, method, tags, summary, description, params, query_metadata, extraMetadata)

    return item


def packItem(call_name, method, tags, summary, description, params, query_metadata, extraMetadata):
    """Generate a swagger specification item using all the given parameters."""
    item = {
        'call_name': call_name,
        'method': method,
        'tags': tags,
        'summary': summary,
        'description': description,
        'params': params,
        'item_properties': None,
        'query': query_metadata['query'],
        'original_query': query_metadata.get('original_query', query_metadata['query'])
    }

    for extraField in extraMetadata:
        if extraField in query_metadata:
            item[extraField] = query_metadata[extraField]

    return item

def get_warning_div(warn):
    return '<div class="errors-wrapper">{}</div>'.format(warn)
