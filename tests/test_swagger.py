# Run using `$ pytest -s`

import unittest
from mock import patch

import grlc.utils  # BUG: grlc.swagger will not import without this import first
from grlc.swagger import build_spec


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


class TestSwagger(unittest.TestCase):
    @patch('github.Github.get_repo')  # Corresponding patch object: mockGithubRepo
    @patch('grlc.utils.GithubLoader.fetchFiles')  # Corresponding patch object: mockLoaderFiles
    @patch('grlc.swagger.process_sparql_query_text', side_effect=mock_process_sparql_query_text)
    def test_github(self, mockQueryText, mockLoaderFiles, mockGithubRepo):
        mockLoaderFiles.return_value = filesInRepo
        mockGithubRepo.return_value = []

        user = 'testuser'
        repo = 'testrepo'
        spec = build_spec(user, repo)

        self.assertEqual(len(spec), len(filesInRepo))


if __name__ == '__main__':
    unittest.main()
