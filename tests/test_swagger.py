# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

# Run using `$ pytest -s`

import unittest
from mock import patch

from grlc.swagger import build_spec

from tests.mock_data import mock_process_sparql_query_text, filesInRepo


class TestSwagger(unittest.TestCase):
    @patch("github.Github.get_repo")  # Corresponding patch object: mockGithubRepo
    @patch(
        "grlc.utils.GithubLoader.fetchFiles"
    )  # Corresponding patch object: mockLoaderFiles
    @patch(
        "grlc.swagger.process_sparql_query_text",
        side_effect=mock_process_sparql_query_text,
    )
    def test_github(self, mockQueryText, mockLoaderFiles, mockGithubRepo):
        mockLoaderFiles.return_value = filesInRepo
        mockGithubRepo.return_value = []

        user = "testuser"
        repo = "testrepo"
        spec, warnings = build_spec(user, repo, git_type="github")

        self.assertEqual(len(spec), len(filesInRepo))


if __name__ == "__main__":
    unittest.main()
