#!/usr/bin/env python

# static.py: static values for the grlc Server
import os
from configparser import ConfigParser

DEFAULT_HOST = None
DEFAULT_PORT = 8088

# XSD datatypes for parsing queries with parameters
XSD_DATATYPES = ["decimal", "float", "double", "integer", "positiveInteger", "negativeInteger", "nonPositiveInteger", "nonNegativeInteger", "long", "int", "short", "byte", "unsignedLong", "unsignedInt", "unsignedShort", "unsignedByte", "dateTime", "date", "gYearMonth", "gYear", "duration", "gMonthDay", "gDay", "gMonth", "string", "normalizedString", "token", "language", "NMTOKEN", "NMTOKENS", "Name", "NCName", "ID", "IDREFS", "ENTITY", "ENTITIES", "QName", "boolean", "hexBinary", "base64Binary", "anyURI", "notation"]

# MIME types for content negotiation
mimetypes = {
    'csv' : 'text/csv; q=1.0, */*; q=0.1',
    'json' : 'application/json; q=1.0, application/sparql-results+json; q=0.8, */*; q=0.1',
    'html' : 'text/html; q=1.0, */*; q=0.1',
    'ttl' : 'text/turtle'
}

# GitHub base URLS
GITHUB_RAW_BASE_URL = 'https://raw.githubusercontent.com/'
GITHUB_API_BASE_URL = 'https://api.github.com/repos/'

# Cache control
# CACHE_CONTROL_POLICY = 'public, max-age=60'
# With the new hash retrieveal and redirect caching becomes obsolete
CACHE_CONTROL_POLICY = 'no-cache'

# Setting headers to use access_token for the GitHub API
config_fallbacks = {
    'github_access_token': '',
    'sparql_endpoint': '',
    'user': '',
    'password': '',
    'server_name': '',
    'local_sparql_dir': '',
    'debug': 'False'
}
config = ConfigParser(config_fallbacks)
config.add_section('auth')
config.add_section('defaults')
config.add_section('local')
config_filename = os.path.join(os.getcwd(), 'config.ini')
print('Reading config file: ', config_filename)
config.read(config_filename)
ACCESS_TOKEN = config.get('auth', 'github_access_token')

# Default endpoint, if none specified elsewhere
DEFAULT_ENDPOINT = config.get('defaults', 'sparql_endpoint')
DEFAULT_ENDPOINT_USER = config.get('defaults', 'user')
DEFAULT_ENDPOINT_PASSWORD = config.get('defaults', 'password')

# Local folder where queries are loaded from
LOCAL_SPARQL_DIR = config.get('local', 'local_sparql_dir')

# server name, used by the Flask app and in the swagger spec
SERVER_NAME = config.get('defaults', 'server_name')

# Logging format (prettier than the ugly standard in Flask)
LOG_FORMAT = '%(asctime)-15s [%(levelname)s] (%(module)s.%(funcName)s) %(message)s'
LOG_DEBUG_MODE = config.getboolean('defaults', 'debug')

# Pattern for INSERT query call names
INSERT_PATTERN = "INSERT DATA { GRAPH ?_g_iri { <s> <p> <o> }}"
