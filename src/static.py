#!/usr/bin/env python

# static.py: static values for the grlc Server

from ConfigParser import SafeConfigParser

DEFAULT_HOST = None
DEFAULT_PORT = 8088

# server name, used by the Flask app and in the swagger spec
SERVER_NAME = "grlc.io"

# XSD datatypes for parsing queries with parameters
XSD_DATATYPES = ["decimal", "float", "double", "integer", "positiveInteger", "negativeInteger", "nonPositiveInteger", "nonNegativeInteger", "long", "int", "short", "byte", "unsignedLong", "unsignedInt", "unsignedShort", "unsignedByte", "dateTime", "date", "gYearMonth", "gYear", "duration", "gMonthDay", "gDay", "gMonth", "string", "normalizedString", "token", "language", "NMTOKEN", "NMTOKENS", "Name", "NCName", "ID", "IDREFS", "ENTITY", "ENTITIES", "QName", "boolean", "hexBinary", "base64Binary", "anyURI", "notation"]

# MIME types for content negotiation
mimetypes = {
    'csv' : 'text/csv; q=1.0, */*; q=0.1',
    'json' : 'application/json; q=1.0, application/sparql-results+json; q=0.8, */*; q=0.1',
    'html' : 'text/html; q=1.0, */*; q=0.1',
    'ttl' : 'text/turtle'
}

# Logging format (prettier than the ugly standard in Flask)
LOG_FORMAT = '%(asctime)-15s [%(levelname)s] (%(module)s.%(funcName)s) %(message)s'

# GitHub base URLS
GITHUB_RAW_BASE_URL = 'https://raw.githubusercontent.com/'
GITHUB_API_BASE_URL = 'https://api.github.com/repos/'

# Cache control
# CACHE_CONTROL_POLICY = 'public, max-age=60'
CACHE_CONTROL_POLICY = 'public, max-age=86400' # 24 hours

# Setting headers to use access_token for the GitHub API
config = SafeConfigParser()
config.read('config.ini')
ACCESS_TOKEN = config.get('auth', 'github_access_token')

# Default endpoint, if none specified elsewhere
DEFAULT_ENDPOINT = config.get('defaults', 'sparql_endpoint')
