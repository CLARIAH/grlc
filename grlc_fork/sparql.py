# # grlc_fork: local modules
# import glogging as glogging
# import static as static

# grlc_fork: ermote modules
import grlc_fork.glogging as glogging
import grlc_fork.static as static

# other imports
from SPARQLWrapper import SPARQLWrapper, CSV, JSON
from flask import jsonify
from collections import defaultdict

# util variables
glogger = glogging.getGrlcLogger(__name__)

SUPPORTED_MIME_FORMATS = defaultdict(
    lambda: JSON, {
        'text/csv': CSV,
        'application/json': JSON
    }
)

MIME_FORMAT = {
    format: mime for mime, format in SUPPORTED_MIME_FORMATS.items()
}

def getResponseText(endpoint, query, requestedMimeType):
    """Returns the result and mimetype of executing the given query against 
    the given endpoint.

    Keyword arguments:
    endpoint - URL of sparql endpoint
    query    - SPARQL query to be executed
    requestedMimeType  Type of content requested. can be:
                'text/csv; q=1.0, */*; q=0.1'
                'application/json'
                etc.
    """
    retFormat = _mimeTypeToSparqlFormat(requestedMimeType)

    client = SPARQLWrapper(endpoint)
    client.setQuery(query)
    client.setReturnFormat(retFormat)
    client.setCredentials(static.DEFAULT_ENDPOINT_USER, static.DEFAULT_ENDPOINT_PASSWORD)
    result = client.queryAndConvert()

    if retFormat==JSON:
        result = jsonify(result)

    return result, MIME_FORMAT[retFormat]

def _mimeTypeToSparqlFormat(mimeType):
    if ';' in mimeType:
        mimeType = mimeType.split(';')[0].strip()
    return SUPPORTED_MIME_FORMATS[mimeType]
