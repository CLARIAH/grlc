from mock import Mock
from os import path
from glob import glob

from collections import namedtuple
from grlc.fileLoaders import LocalLoader

base_url = path.join('tests', 'repo')
def buildEntry(entryName):
    entryName = entryName.replace(base_url, '')

    # Named tuple containing properties of mocked github ContentFile
    MockGithubContentFile = namedtuple('MockGithubContentFile', 'download_url name path type decoded_content')
    return MockGithubContentFile(
        download_url = entryName,
        name = entryName,
        path = entryName,
        type = u'file',
        decoded_content = 'FAKE FILE CONTENT'.encode() # Because Github ContentFile object contains bytes.
    )
mock_files = [ buildEntry(f) for f in glob(path.join(base_url, '*')) ]

class MockGithubRepo:
    def get_contents(self, filename, ref=None):
        if filename == "":
            return mock_files
        else:
            for f in mock_files:
                if filename in f.name: # filenames contain extra /
                    return f
            return None


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
        u'decoded_content': 'CONTENT ?'.encode() # Because Github ContentFile object contains bytes.
    }
]

mockLoader = LocalLoader(base_url)