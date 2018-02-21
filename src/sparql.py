from SPARQLWrapper import SPARQLWrapper, CSV, JSON
from flask import jsonify

SPARQL_FORMATS = {
    'text/csv': CSV,
    'application/json': JSON
}

def selectReturnFormat(contentType):
    return SPARQL_FORMATS[contentType] if contentType in SPARQL_FORMATS else CSV

def executeSPARQLQuery(endpoint, query, retformat):
    client = SPARQLWrapper(endpoint)
    client.setQuery(query)
    client.setReturnFormat(retformat)
    result = client.queryAndConvert()

    if retformat==JSON:
        result = jsonify(result)

    return result
