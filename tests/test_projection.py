import unittest

from grlc.projection import project

from tests.mock_data import mock_sparqlResponse

class TestProjection(unittest.TestCase):
    def xtest_project_error(self):
        projectionScript = 'This projection script has invalid syntax'
        projection = project(mock_sparqlResponse, projectionScript)
        self.assertIn('status', projection, 'Should contain a status')
        self.assertEqual(projection['status'], 'error', 'Status should be error')

    def test_project_success_simple(self):
        projectionScript = 'dataOut = {}\n'
        projection = project(mock_sparqlResponse, projectionScript)
        self.assertIsInstance(projection, dict)
        self.assertEqual(projection, {})

    def test_project_success_not_so_simple(self):
        projectionScript = '''
from pythonql.Executor import *

dataOut = [
    select (country, capital)
    for item in dataIn['results']['bindings']
    let country = item['country_name']['value']
    let capital = item['capital_name']['value']
]
        '''
        projection = project(mock_sparqlResponse, projectionScript)
        self.assertIsInstance(projection, list, 'Projection should be a list')
        for item in projection:
            itemDict = item.getDict()
            self.assertIn('country', itemDict, 'List items should contain a country')
            self.assertIn('capital', itemDict, 'List items should contain a capital')
