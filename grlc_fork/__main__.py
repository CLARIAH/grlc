# /*
# * SPDX-License-Identifier: MIT
# * SPDX-FileCopyrightText: Copyright (c) 2022 Orange SA
# *
# * Author: Mihary RANAIVOSON
# * Modifications: 
#     - Formerly called server.py
#     - Change and add paths of some routes
# */


# # grlc_fork: local modules
# import static as static
# from utils import api_docs_template, swagger_spec, query
# import glogging as glogging

# grlc_fork: remote modules
import grlc_fork.static as static
from grlc_fork.utils import api_docs_template, swagger_spec, query
import grlc_fork.glogging as glogging

# other imports
from flask import Flask, request, jsonify, render_template, make_response
from flask_cors import CORS

# util variables
glogger = glogging.getGrlcLogger(__name__)

app = Flask(__name__)
# cors = CORS(
#     app, 
#     resources={r"/*": {"origins": "*"}}
# )
CORS(app)





#############################
###     Server routes     ###
#############################

@app.route('/')
def grlc():
    """Grlc landing page."""
    resp = make_response(render_template('index.html'))
    return resp




#############################
### Routes for local APIs ###
#############################

# Spec generation, front-end
@app.route('/api-local', methods=['GET'], strict_slashes=False)
@app.route('/api/local/local', methods=['GET'], strict_slashes=False)  # backward compatibility route
def api_docs_local():
    """Grlc API page for local routes."""
    return api_docs_template()

# Spec generation, JSON
@app.route('/api-local/swagger', methods=['GET'])
@app.route('/api/local/local/swagger', methods=['GET'], strict_slashes=False)  # backward compatibility route
def swagger_spec_local():
    """Swagger spec for local routes."""
    return swagger_spec(user=None, repo=None, sha=None, content=None)

# Callname execution
@app.route('/api-local/<query_name>', methods=['GET', 'POST'])
@app.route('/api-local/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api/local/local/<query_name>', methods=['GET', 'POST'], strict_slashes=False)  # backward compatibility route
@app.route('/api/local/local/<query_name>.<content>', methods=['GET', 'POST'], strict_slashes=False)  # backward compatibility route
def query_local(query_name, content=None):
    """SPARQL query execution for local routes."""
    return query(user=None, repo=None, query_name=query_name, content=content)




################################
### Routes for URL HTTP APIs ###
################################

# Spec generation, front-end
@app.route('/api-url', methods=['POST', 'GET'], strict_slashes=False)
def api_docs_param():
    """Grlc API page for specifications loaded via http."""
    # Get queries provided by params
    spec_url = request.args['specUrl']
    glogger.info("Spec URL: {}".format(spec_url))
    return api_docs_template()

# Spec generation, JSON
@app.route('/api-url/swagger', methods=['GET'])
def swagger_spec_param():
    """Swagger spec for specifications loaded via http."""
    spec_url = request.args['specUrl']
    glogger.info("Spec URL: {}".format(spec_url))
    return swagger_spec(user=None, repo=None, spec_url=spec_url)

# Callname execution
@app.route('/api-url/<query_name>', methods=['GET', 'POST'])
@app.route('/api-url/<query_name>.<content>', methods=['GET', 'POST'])
def query_param(query_name, content=None):
    """SPARQL query execution for specifications loaded via http."""
    spec_url = request.args['specUrl']
    glogger.debug("Spec URL: {}".format(spec_url))
    return query(user=None, repo=None, query_name=query_name, spec_url=spec_url, content=content)




##############################
### Routes for GitHub APIs ###
##############################

# Spec generation, front-end
@app.route('/api-github/<user>/<repo>', strict_slashes=False)
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>', strict_slashes=False)
@app.route('/api-github/<user>/<repo>/api-docs')
@app.route('/api-github/<user>/<repo>/commit/<sha>')
@app.route('/api-github/<user>/<repo>/commit/<sha>/api-docs')
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>/commit/<sha>')
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>/commit/<sha>/api-docs')
def api_docs_github(user, repo, subdir=None, sha=None):
    """Grlc API page for specifications loaded from a Github repo."""
    return api_docs_template()

# Spec generation, JSON
@app.route('/api-github/<user>/<repo>/swagger', methods=['GET'])
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>/swagger', methods=['GET'])
@app.route('/api-github/<user>/<repo>/commit/<sha>/swagger')
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>/commit/<sha>/swagger')
@app.route('/api-github/<user>/<repo>/<path:subdir>/commit/<sha>/swagger')
def swagger_spec_github(user, repo, subdir=None, sha=None):
    """Swagger spec for specifications loaded from a Github repo."""
    return swagger_spec(user, repo, subdir=subdir, spec_url=None, sha=sha, content=None, git_type="github")

# Callname execution
@app.route('/api-github/<user>/<repo>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-github/<user>/<repo>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-github/<user>/<repo>/commit/<sha>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>/commit/<sha>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-github/<user>/<repo>/commit/<sha>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-github/<user>/<repo>/subdir/<path:subdir>/commit/<sha>/<query_name>.<content>', methods=['GET', 'POST'])
def query_github(user, repo, query_name, subdir=None, sha=None, content=None):
    """SPARQL query execution for specifications loaded from a Github repo."""
    return query(user, repo, query_name, subdir=subdir, sha=sha, content=content, git_type="github")




##############################
### Routes for GitLab APIs ###
##############################

# Spec generation, front-end
@app.route('/api-gitlab/<user>/<repo>', strict_slashes=False)
@app.route('/api-gitlab/<user>/<repo>/branch/<branch>', strict_slashes=False)
@app.route('/api-gitlab/<user>/<repo>/subdir/<path:subdir>', strict_slashes=False)
@app.route('/api-gitlab/<user>/<repo>/branch/<branch>/subdir/<path:subdir>', strict_slashes=False)
@app.route('/api-gitlab/<user>/<repo>/api-docs')
@app.route('/api-gitlab/<user>/<repo>/commit/<sha>')
@app.route('/api-gitlab/<user>/<repo>/commit/<sha>/api-docs')
@app.route('/api-gitlab/<user>/<repo>/subdir/<path:subdir>/commit/<sha>')
@app.route('/api-gitlab/<user>/<repo>/subdir/<path:subdir>/commit/<sha>/api-docs')
def api_docs_gitlab(user, repo, subdir=None, sha=None, branch='main'):
    """Grlc API page for specifications loaded from a Github repo."""
    glogger.debug("Entry in function: __main__.api_docs_gitlab")
    return api_docs_template()

# Spec generation, JSON
@app.route('/api-gitlab/<user>/<repo>/swagger', methods=['GET'])
@app.route('/api-gitlab/<user>/<repo>/branch/<branch>/swagger', methods=['GET'])
@app.route('/api-gitlab/<user>/<repo>/subdir/<path:subdir>/swagger', methods=['GET'])
@app.route('/api-gitlab/<user>/<repo>/branch/<branch>/subdir/<path:subdir>/swagger', methods=['GET'])
@app.route('/api-gitlab/<user>/<repo>/commit/<sha>/swagger')
@app.route('/api-gitlab/<user>/<repo>/subdir/<path:subdir>/commit/<sha>/swagger')
@app.route('/api-gitlab/<user>/<repo>/<path:subdir>/commit/<sha>/swagger')
def swagger_spec_gitlab(user, repo, subdir=None, sha=None, branch='main'):
    """Swagger spec for specifications loaded from a Github repo."""
    glogger.debug("Entry in function: __main__.swagger_spec_gitlab")
    return swagger_spec(user, repo, subdir=subdir, spec_url=None, sha=sha, content=None, git_type="gitlab", branch=branch)

# Callname execution
@app.route('/api-gitlab/<user>/<repo>/query/<query_name>', methods=['GET', 'POST'])
@app.route('/api-gitlab/<user>/<repo>/query/branch/<branch>/<query_name>', methods=['GET','POST'])
@app.route('/api-gitlab/<user>/<repo>/query/subdir/<path:subdir>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-gitlab/<user>/<repo>/query/branch/<branch>/subdir/<path:subdir>/<query_name>', methods=['GET','POST'])
@app.route('/api-gitlab/<user>/<repo>/query/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-gitlab/<user>/<repo>/query/subdir/<path:subdir>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-gitlab/<user>/<repo>/query/commit/<sha>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-gitlab/<user>/<repo>/query/subdir/<path:subdir>/commit/<sha>/<query_name>', methods=['GET', 'POST'])
@app.route('/api-gitlab/<user>/<repo>/query/commit/<sha>/<query_name>.<content>', methods=['GET', 'POST'])
@app.route('/api-gitlab/<user>/<repo>/query/subdir/<path:subdir>/commit/<sha>/<query_name>.<content>', methods=['GET', 'POST'])
def query_gitlab(user, repo, query_name, subdir=None, sha=None, content=None, branch='main'):
    """SPARQL query execution for specifications loaded from a Github repo."""
    glogger.debug("Entry in function: __main__.query_gitlab")
    return query(user, repo, query_name, subdir=subdir, sha=sha, content=content, git_type="gitlab", branch=branch)




##############################
###      Main Thread       ###
##############################

if __name__ == '__main__':
    app.run(host=static.SERVER_HOST, port=static.SERVER_PORT, debug=True)
