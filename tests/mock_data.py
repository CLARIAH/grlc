# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

from mock import Mock
from os import path
from glob import glob

from collections import namedtuple
from grlc.fileLoaders import LocalLoader
import base64

base_url = path.join('tests', 'repo')

def buildGHEntry(entryName):
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

def buildGLEntry(entryName):
    entryName = entryName.replace(base_url, '')

    return { 'type': 'blob',
            'name': entryName
        }

mock_gh_files = [ buildGHEntry(f) for f in glob(path.join(base_url, '*')) ]
mock_gl_files = [ buildGLEntry(f) for f in glob(path.join(base_url, '*')) ]

class MockGithubRepo:
    def get_contents(self, filename, ref=None):
        if filename == "":
            return mock_gh_files
        else:
            for f in mock_gh_files:
                if filename in f.name: # filenames contain extra /
                    return f
            return None


class MockGitlabModule:
    def __init__(self) -> None:
        gl_repo = Mock()

        gl_repo.repository_tree = Mock(return_value=mock_gl_files)
        gl_repo.files.get.side_effect = self.gl_files_content
        gl_repo.default_branch = 'main'
    
        self.projects = Mock()
        self.projects.get.return_value = gl_repo

    def gl_files_content(self, file_path, ref):
        '''Returns none if the file is not in the known repo'''
        for glf in mock_gl_files:
            if file_path in glf['name']: # filenames contain extra /
                f = Mock()
                f_content = "The text of a file"
                f.content = base64.b64encode(f_content.encode("utf-8"))
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