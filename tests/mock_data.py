from mock import Mock
from os import path
from glob import glob

base_url = path.join('tests', 'repo')
def buildEntry(entryName):
    entryName = entryName.replace(base_url, '')
    return {
        u'download_url': entryName,
         u'name': entryName,
         u'path': entryName,
         u'type': u'file'
    }
mock_files = [ buildEntry(f) for f in glob(path.join(base_url, '*')) ]

def mock_requestsGithub(uri, headers={}, params={}):
    if uri.endswith('contents'):
        return_value = Mock(ok=True)
        return_value.json.return_value = mock_files
        return return_value
    else:
        targetFile = uri.replace('https://raw.githubusercontent.com/fakeuser/fakerepo/master/', path.join(base_url, ''))
        if path.exists(targetFile):
            f = open(targetFile, 'r')
            lines = f.readlines()
            text = ''.join(lines)
            return_value = Mock(status_code=200)
            return_value.text = text
            return return_value
        else:
            return_value = Mock(status_code=404)
            return return_value

def mock_requestsUrl(url, headers={}, params={}):
    url = url.replace('http://example.org/', 'tests/repo/')
    f = open(url, 'r')
    lines = f.readlines()
    text = ''.join(lines)
    return_value = Mock(status_code=200)
    return_value.text = text

    return return_value

mock_simpleSparqlResponse = {
    "head": { "link": [], "vars": ["p", "o"] },
    "results": {
        "bindings": [
            { "p": { "type": "string", "value": "p1" }	, "o": { "type": "string", "value": "o1" }},
            { "p": { "type": "string", "value": "p2" }	, "o": { "type": "string", "value": "o2" }},
            { "p": { "type": "string", "value": "p3" }	, "o": { "type": "string", "value": "o3" }},
            { "p": { "type": "string", "value": "p4" }	, "o": { "type": "string", "value": "o4" }},
            { "p": { "type": "string", "value": "p5" }	, "o": { "type": "string", "value": "o5" }}
        ]
    }
}

def mock_process_sparql_query_text(query_text, raw_repo_uri, call_name, extraMetadata):
    mockItem = {
        "status": "This is a mock item",
        "call_name": call_name
    }
    return mockItem


filesInRepo = [
    {
        u'name': u'fakeFile1.rq',
        u'download_url': u'https://example.org/path/to/fakeFile.rq',
    }
]
