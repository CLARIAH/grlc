# /*
# * SPDX-License-Identifier: MIT
# * SPDX-FileCopyrightText: Copyright (c) 2022 Orange SA
# *
# * Author: Mihary RANAIVOSON
# * Modifications: Change arguments to parse
# */


from configparser import ConfigParser
import os


# config parser
configParser = ConfigParser()
config_filepath = os.path.join(os.getcwd(), 'config.ini')
configParser.read(config_filepath)


#-----------------------


# server
SERVER_HOST = configParser.get('server', 'host', fallback='127.0.0.1')
SERVER_PORT = configParser.get('server', 'port', fallback='8088')


# endpoint
DEFAULT_ENDPOINT          = configParser.get('endpoint', 'url', fallback='http://127.0.0.1:8890/sparql')
DEFAULT_ENDPOINT_USER     = configParser.get('endpoint', 'user', fallback='')
DEFAULT_ENDPOINT_PASSWORD = configParser.get('endpoint', 'user', fallback='')


# auth
ACCESS_TOKEN = configParser.get('auth', 'git_access_token', fallback='')


# log
LOG_LEVEL = configParser.get('log', 'level', fallback='info')


# api_local
LOCAL_SPARQL_DIR = configParser.get('api_local', 'sparql_dir', fallback='.')


# api_url


# api_github


# api_gitlab
GITLAB_URL    = configParser.get('api_gitlab', 'gitlab_url', fallback='https://gitlab')


#-----------------------


# SERVER_NAME
SERVER_NAME = SERVER_HOST + ':' + SERVER_PORT


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


# Pattern for INSERT query call names
INSERT_PATTERN = "INSERT DATA { GRAPH ?_g_iri { <s> <p> <o> }}"


# Log
LOG_FORMAT = '%(asctime)-15s [%(levelname)s] (%(module)s.%(funcName)s) %(message)s'