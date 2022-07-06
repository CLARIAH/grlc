# /*
# * SPDX-License-Identifier: MIT
# * SPDX-FileCopyrightText: Copyright (c) 2022 Orange SA
# *
# * Author: Mihary RANAIVOSON
# * Modifications: 
# *    - Deletion of TPFQueries
# *    - Update of some functions in order to take account Gitlab repo
# */


# # grlc_fork: local modules
# import static as static
# import gquery as gquery
# import pagination as pageUtils
# from prov import grlcPROV
# from fileLoaders import GithubLoader, LocalLoader, URLLoader, GitlabLoader
# from queryTypes import qType
# import glogging as glogging
# import swagger as swagger

# grlc_fork: remote modules
import grlc_fork.static as static
import grlc_fork.gquery as gquery
import grlc_fork.pagination as pageUtils
from grlc_fork.prov import grlcPROV
from grlc_fork.fileLoaders import GithubLoader, LocalLoader, URLLoader, GitlabLoader
from grlc_fork.queryTypes import qType
import grlc_fork.glogging as glogging
import grlc_fork.swagger as swagger

# other imports
import re
import requests
import json
from rdflib import Graph
import SPARQLTransformer
from flask import request, jsonify, render_template, make_response

# util variables
glogger = glogging.getGrlcLogger(__name__)






def relative_path():
    """Generate relative path for the current route. This is used to build relative paths when rendering templates."""
    path = request.path
    path = '.' + '/..' * (path.count('/') - 1)
    return path





def api_docs_template():
    """Generate Grlc API page."""
    glogger.debug("Entry in function: utils.api_docs_template")
    return render_template('api-docs.html', relative_path=relative_path())





def swagger_spec(user, repo, subdir=None, spec_url=None, sha=None, content=None, git_type=None, branch='main'):
    """ Generate swagger specification """
    glogger.debug("Entry in function: utils.swagger_spec")
    glogger.info("-----> Generating swagger spec for /{}/{}, subdir {}, params {}, on commit {}".format(user, repo, subdir, spec_url, sha))

    swag = build_swagger_spec(user, repo, subdir, spec_url, sha, static.SERVER_NAME, git_type, branch)

    resp_spec = make_response(jsonify(swag))
    resp_spec.headers['Content-Type'] = 'application/json'

    resp_spec.headers['Cache-Control'] = static.CACHE_CONTROL_POLICY  # Caching JSON specs for 15 minutes

    glogger.info("-----> API spec generation for /{}/{}, subdir {}, params {}, on commit {} complete".format(user, repo, subdir, spec_url, sha))
    glogger.debug("Exit of function: utils.swagger_spec")
    return resp_spec





def query(user, repo, query_name, subdir=None, spec_url=None, sha=None, content=None, git_type=None, branch='main'):
    """Execute SPARQL query for a specific grlc-generated API endpoint"""
    glogger.debug("Entry in function: utils.query")
    glogger.info("-----> Executing call name at /{}/{}/{}/{} on commit {}".format(user, repo, subdir, query_name, sha))
    glogger.debug("Request accept header: " + request.headers["Accept"])

    requestArgs = request.args
    acceptHeader = request.headers['Accept']
    requestUrl = request.url
    formData = request.form
    method = request.method

    query_response, status, headers = dispatch_query(user, repo, query_name, subdir, spec_url,
                                                        sha=sha, content=content, requestArgs=requestArgs,
                                                        acceptHeader=acceptHeader,
                                                        requestUrl=requestUrl, formData=formData, method=method, git_type=git_type, branch=branch)

    glogger.debug("Exit of function: utils.query")                              
    return make_response(query_response, status, headers)





def getLoader(user, repo, subdir=None, spec_url=None, sha=None, prov=None, git_type=None, branch='main'):
    """Build a fileLoader (LocalLoader, GithubLoader, URLLoader) for the given parameters."""
    glogger.debug("Entry in function: utils.getLoader")

    if user is None and repo is None and not spec_url:
        loader = LocalLoader()
    elif spec_url:
       loader = URLLoader(spec_url)
    else:
        if git_type == 'github':
            loader = GithubLoader(user, repo, subdir, sha, prov)
        else:
            loader = GitlabLoader(user, repo, subdir, sha, prov, branch)

    glogger.debug("Exit of function: utils.getLoader")
    return loader





def build_spec(user, repo, subdir=None, sha=None, prov=None, extraMetadata=[], branch='main'):
    """Build grlc specification for the given github user / repo.
    
    Deprecated."""
    glogger.debug("Entry in function: utils.build_spec")
    glogger.warning("grlc.utils.build_spec is deprecated and will " \
                    "be removed in the future. Use grlc.swagger.build_spec instead.")
    items, _ = swagger.build_spec(user, repo, subdir, sha, prov, extraMetadata, branch)
    glogger.debug("Exit of function: utils.build_spec")
    return items





def build_swagger_spec(user, repo, subdir, spec_url, sha, serverName, git_type, branch='main'):
    """Build grlc specification for the given github user / repo in swagger format."""
    glogger.debug("Entry in function: utils.build_swagger_spec")
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
    spec, warnings = swagger.build_spec(user, repo, subdir, spec_url, sha, prov_g, [], branch)
    # Use items to build API paths
    for item in spec:
        swag['paths'][item['call_name']] = swagger.get_path_for_item(item)

     # TODO: Add bootstrap style to top level HTML
    # Without a better place to display warnings, we can make them part of the description.
    if 'description' not in swag['info']:
        swag['info']['description'] = ''
    for warn in warnings:
        swag['info']['description'] += swagger.get_warning_div(warn)

    if prov_g:
        prov_g.end_prov_graph()
        swag['prov'] = prov_g.serialize(format='turtle')

    glogger.debug("Exit of function: utils.build_swagger_spec")
    return swag





def dispatch_query(user, repo, query_name, subdir=None, spec_url=None, sha=None, 
        content=None, requestArgs={}, acceptHeader='application/json',
        requestUrl='http://', formData={}, method='POST', git_type=None, branch='main'):
    """Executes the specified SPARQL or TPF query."""
    glogger.debug("Entry in function: utils.dispatch_query")

    # params for query
    loader         = getLoader(user, repo, subdir, spec_url, sha=sha, prov=None, git_type=git_type, branch=branch)
    query, _       = loader.getTextForName(query_name)
    endpoint, _    = gquery.guess_endpoint_uri(query, loader)
    data_or_params = { 'query': query }
    headers        = { 'Accept': acceptHeader }

    # query response
    if method == 'POST' or method == 'GET':
        if method == 'POST':
            response = requests.post(url=endpoint, data=data_or_params, headers=headers)
        else:
            response = requests.get(url=endpoint, params=data_or_params, headers=headers)
        resp = response.text
        resp = resp.replace('\\n', '\n') if (acceptHeader == 'application/json') else resp
        status = 200
    else:
        resp = "Method " + method + " not supported"
        status = 400

    # return
    glogger.debug("Exit of function: utils.dispatch_query")
    return resp, status, headers
