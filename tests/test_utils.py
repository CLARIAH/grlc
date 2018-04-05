# Run using `$ pytest -s`

import unittest
from mock import patch

from grlc.utils import build_spec

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

class TestUtils(unittest.TestCase):
    @patch('grlc.utils.GithubLoader.fetchFiles')
    @patch('grlc.utils.process_sparql_query_text', side_effect=mock_process_sparql_query_text)
    def test_github(self, mockQueryText, mockLoaderFiles):
        mockLoaderFiles.return_value = filesInRepo

        user = 'testuser'
        repo = 'testrepo'
        spec = build_spec(user, repo)

        self.assertEquals(len(spec), len(filesInRepo))

if __name__ == '__main__':
    unittest.main()
