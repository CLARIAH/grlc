# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

from SPARQLWrapper import SPARQLWrapper, CSV, JSON
from flask import jsonify
from collections import defaultdict

import static as static
import grlc.glogging as glogging

glogger = glogging.getGrlcLogger(__name__)

# Default value is JSON
SUPPORTED_MIME_FORMATS = defaultdict(
    lambda: JSON, {"text/csv": CSV, "application/json": JSON}
)

MIME_FORMAT = {format: mime for mime, format in SUPPORTED_MIME_FORMATS.items()}
DEFAULT_USER_AGENT = "grlc/sparql"


# TODO: check if this code is still used anywhere
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
    if hasattr(client, "setAgent"):
        client.setAgent(DEFAULT_USER_AGENT)
    elif hasattr(client, "addCustomHttpHeader"):
        client.addCustomHttpHeader("User-Agent", DEFAULT_USER_AGENT)
    client.setQuery(query)
    client.setReturnFormat(retFormat)
    client.setCredentials(
        static.DEFAULT_ENDPOINT_USER, static.DEFAULT_ENDPOINT_PASSWORD
    )
    result = client.queryAndConvert()

    if retFormat == JSON:
        result = jsonify(result)

    return result, MIME_FORMAT[retFormat]


def _mimeTypeToSparqlFormat(mimeType):
    if ";" in mimeType:
        mimeType = mimeType.split(";")[0].strip()
    return SUPPORTED_MIME_FORMATS[mimeType]
