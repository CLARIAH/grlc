# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

import unittest
from mock import patch

from tests.mock_data import mock_process_sparql_query_text, filesInRepo


class TestGrlc(unittest.TestCase):
    """Test grlc has been installed"""

    def test_grlc(self):
        import grlc


class TestGrlcLib(unittest.TestCase):
    """Test grlc can be used as a library"""

    @patch("github.Github.get_repo")  # Corresponding patch object: mockGithubRepo
    @patch(
        "grlc.utils.GithubLoader.fetchFiles"
    )  # Corresponding patch object: mockLoaderFiles
    @patch(
        "grlc.swagger.process_sparql_query_text",
        side_effect=mock_process_sparql_query_text,
    )
    def test_build_spec(self, mockQueryText, mockLoaderFiles, mockGithubRepo):
        mockLoaderFiles.return_value = filesInRepo
        mockGithubRepo.return_value = []

        """Using grlc as a library"""
        import grlc.swagger as swagger

        user = "testuser"
        repo = "testrepo"
        spec, warning = swagger.build_spec(user=user, repo=repo, git_type="github")

        # Repo contains one JSON file which is not a query, and should be ignored
        self.assertEqual(len(spec), len(filesInRepo) - 1)


if __name__ == "__main__":
    unittest.main()
