import unittest
import six
# from mock import patch

from grlc.fileLoaders import LocalLoader, GithubLoader
from grlc.queryTypes import qType


class TestGithubLoader(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.user = 'diveplus'
        self.repo = 'queries'
        self.loader = GithubLoader(self.user, self.repo, None, None)

    def test_fetchFiles(self):
        files = self.loader.fetchFiles()

        # Should return a list of file items
        self.assertIsInstance(files, list, "Should return a list of file items")

        # Should have N files (where N=15)
        self.assertEquals(len(files), 15, "Should return correct number of files")

        # File items should have a download_url
        for fItem in files:
            self.assertIn('download_url', fItem, "File items should have a download_url")

    def test_getRawRepoUri(self):
        repoUri = self.loader.getRawRepoUri()

        # Should be a string
        self.assertIsInstance(repoUri, six.string_types, "Should be a string")

        # For URI shoud contain user / repo
        self.assertIn(self.user, repoUri, "Should contain user")
        self.assertIn(self.repo, repoUri, "Should contain repo")

    def test_getTextFor(self):
        files = self.loader.fetchFiles()

        # the contents of each file
        for fItem in files:
            text = self.loader.getTextFor(fItem)

            # Should be some text
            self.assertIsInstance(text, six.string_types, "Should be some text")

            # Should be non-empty for existing items
            self.assertGreater(len(text), 0, "Should be non-empty")

        # Should raise exception for invalid file items
        with self.assertRaises(Exception, message="Should raise exception for invalid file items"):
            text = self.loader.getTextFor( { } )

    def test_getTextForName(self):
        testableNames = [
            ('detailsAction', qType['SPARQL']),
            ('getCollections', qType['SPARQL']),
            ('getSearchQuery', qType['SPARQL']),
        ]
        for name, expectedType in testableNames:
            text, actualType = self.loader.getTextForName(name)
            self.assertEqual(expectedType, actualType, "Query type should match %s != %s"%(expectedType, actualType))

class TestLocalLoader(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.loader = LocalLoader('./tests/repo/')

    def test_fetchFiles(self):
        files = self.loader.fetchFiles()

        # Should return a list of file items
        self.assertIsInstance(files, list, "Should return a list of file items")

        # Should have N files (where N=4)
        self.assertEquals(len(files), 4, "Should return correct number of files")

        # File items should have a download_url
        for fItem in files:
            self.assertIn('download_url', fItem, "File items should have a download_url")

    def test_getRawRepoUri(self):
        repoUri = self.loader.getRawRepoUri()

        # Should be a string
        self.assertIsInstance(repoUri, six.string_types, "Should be a string")

        # For local repo, should be empty ?
        self.assertEqual(repoUri, "", "Should be an empty string")

    def test_getTextFor(self):
        files = self.loader.fetchFiles()

        # the contents of each file
        for fItem in files:
            text = self.loader.getTextFor(fItem)

            # Should be some text
            self.assertIsInstance(text, six.string_types, "Should be some text")

            # Should be non-empty for existing items
            self.assertGreater(len(text), 0, "Should be non-empty")

        # Should raise exception for invalid file items
        with self.assertRaises(Exception, message="Should raise exception for invalid file items"):
            text = self.loader.getTextFor( { } )

    def test_getTextForName(self):
        testableNames = [
            ('test-rq', qType['SPARQL']),
            ('test-sparql', qType['SPARQL']),
            ('test-tpf', qType['TPF'])
        ]
        for name, expectedType in testableNames:
            text, actualType = self.loader.getTextForName(name)
            self.assertEqual(expectedType, actualType, "Query type should match %s != %s"%(expectedType, actualType))

if __name__ == '__main__':
    unittest.main()
