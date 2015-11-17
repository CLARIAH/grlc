#!/usr/bin/env python

from flask import Flask, request, jsonify, render_template
import urllib2
import json
from SPARQLWrapper import SPARQLWrapper, JSON
import StringIO
import logging
import sys

app = Flask(__name__)
# stream_handler = logging.StreamHandler(sys.stdout)
# stream_handler.setLevel(logging.DEBUG)
# app.logger.addHandler(stream_handler)

def guess_endpoint_uri(rq):
    '''
    Guesses the endpoint URI from (in this order):
    - An #+Endpoint decorator
    - A endpoint.txt file in the repo
    Otherwise assigns a default one
    '''
    endpoint = 'http://dbpedia.org/sparql'

    try:
        buf = StringIO.StringIO(rq)
        endpoint_line = buf.readline()
        endpoint = endpoint_line.split("#+endpoint: ")[1]
        app.logger.debug("Decorator guessed endpoint: " + endpoint)
    except ValueError as e:
        app.logger.error("Couldn't guess endpoint from the query file")
        pass

    return endpoint

@app.route('/')
def hello():
    return 'This is apicrap, it creates crappy apis out of your github stored SPARQL queries for the lulz'

@app.route('/<user>/<repo>/<query>')
def query(user, repo, query):
    app.logger.debug("Got request at /" + user + "/" + repo + "/" + query)
    app.logger.debug("Request accept header: " +request.headers["Accept"])
    raw_repo_uri = 'https://raw.githubusercontent.com/' + user + '/' + repo + '/master/'
    raw_query_uri = raw_repo_uri + query + '.rq'
    stream = urllib2.urlopen(raw_query_uri)
    raw_query = stream.read()
    
    endpoint = guess_endpoint_uri(raw_query)
    app.logger.debug("Guessed endpoint for this query: " + endpoint)
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(raw_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return jsonify(results)

@app.route('/<user>/<repo>/api-docs')
def api_docs(user, repo):
    return render_template('api-docs.html', user=user, repo=repo)

@app.route('/<user>/<repo>/spec')
def swagger_spec(user, repo):
    app.logger.debug("Generating swagger spec for /" + user + "/" + repo)
    api_repo_uri = 'https://api.github.com/repos/' + user + '/' + repo
    stream = urllib2.urlopen(api_repo_uri)
    resp = json.load(stream)
    swag = {}
    swag['swagger'] = '2.0'
    swag['info'] = {'version': '1.0', 'title': resp['name'], 'contact': {'name': resp['owner']['login'], 'url': resp['owner']['url']}, 'license': {'name' : 'licensename', 'url': 'licenseurl'}}
    swag['host'] = 'apicrap.amp.ops.few.vu.nl'
    swag['basePath'] = '/' + user + '/' + repo + '/'
    swag['schemes'] = ['http']
    swag['paths'] = {}
    
    api_repo_content_uri = api_repo_uri + '/contents'
    stream = urllib2.urlopen(api_repo_content_uri)
    resp = json.load(stream)
    # Fetch all .rq files
    for c in resp:
        if ".rq" in c['name']:
            call_name = c['name'].split('.')[0]
            swag['paths'][call_name] = {}
            swag['paths'][call_name]["get"] = {"tags" : ["foo", "bar"],
                                               "summary" : "summary",
                                               "produces" : ["application/json", "text/csv"],
                                               "responses": {
                                                   "200" : {
                                                       "description" : "pet response",
                                                       "schema" : {
                                                           "type" : "object",
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
    
    return jsonify(swag)

# DEPRECATED
# Do something on github pushes?
@app.route('/sparql', methods = ['POST'])
def sparql():
    push = json.loads(request.data)
    # One push may contain many commits
    for c in push['commits']:
        # We only look for .rq files
        for a in c['added']:
            if '.rq' in a:
                # New query added
                add_query(push['repository']['full_name'], a)
        print c['added']
        print c['removed']
        print c['modified']
    
        return 'foo'

if __name__ == '__main__':
    app.run(port=8088, debug=True)
