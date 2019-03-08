import unittest
import six
import rdflib
from mock import patch, Mock

from grlc.fileLoaders import LocalLoader
import grlc.gquery as gquery
import grlc.utils as utils

from flask import Flask


class TestGQuery(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.loader = LocalLoader('./tests/repo/')
        self.app = Flask('unittests')

    def test_guess_endpoint(self):
        with self.app.test_request_context('/?endpoint=http://url-endpoint/from-url/sparql'):
            endpoint, _ = gquery.guess_endpoint_uri('', self.loader)
            self.assertIn('from-url', endpoint,
                          'Should match endpoint given in url')

        with self.app.test_request_context('/'):
            endpoint, _ = gquery.guess_endpoint_uri('', self.loader)
            self.assertIn('from-file', endpoint,
                          'Should match endpoint in endpoint.txt')

            rq, _ = self.loader.getTextForName('test-rq')
            endpoint, _ = gquery.guess_endpoint_uri(rq, self.loader)
            self.assertIn('from-decorator', endpoint,
                          'Should match endpoint in test-rq.rq')

    def test_get_parameters(self):
        rq, _ = self.loader.getTextForName('test-rq')

        params = gquery.get_parameters(rq, '', '', {})
        for paramName, param in params.items():
            self.assertIn('name', param, 'Should have a name')
            self.assertIn('type', param, 'Should have a type')
            self.assertIn('required', param, 'Should have a required')

            orig = param['original']
            if '_iri' in orig:
                self.assertEqual(param['type'], 'string', 'Should be type string')
                self.assertEqual(param['format'], 'iri', 'Should be format iri')
            if '_number' in orig:
                self.assertEqual(param['type'], 'number',
                                 'Should be type number')
            if '_literal' in orig:
                self.assertEqual(param['type'], 'literal',
                                 'Should be type literal')
            if '_en' in orig:
                self.assertEqual(param['type'], 'literal',
                                 'Should be type literal')
                self.assertEqual(param['lang'], 'en', 'Should be en language')
            if '_integer' in orig:
                self.assertEqual(
                    param['datatype'], 'xsd:integer', 'Should be type xsd:integer')
            if '_xsd_date' in orig:
                self.assertEqual(param['datatype'],
                                 'xsd:date', 'Should be type xsd:date')

    @patch('requests.get')
    def test_get_enumeration(self, mock_get):
        mock_get.return_value = Mock(ok=True)
        mock_get.return_value.json.return_value = {
            'results': {
                'bindings': [
                    {'o1': {'value': 'v1'}},
                    {'o1': {'value': 'v2'}}
                ]
            }
        }

        rq, _ = self.loader.getTextForName('test-rq')
        metadata = {'enumerate': 'o1'}
        enumeration = gquery.get_enumeration(rq, 'o1', 'http://mock-endpoint/sparql', metadata)
        self.assertIsInstance(enumeration, list, 'Should return a list of values')
        self.assertEqual(len(enumeration), 2, 'Should have two elements')

    def test_get_static_enumeration(self):
        rq, _ = self.loader.getTextForName('test-enum')

        metadata = gquery.get_yaml_decorators(rq)
        self.assertIn('enumerate', metadata, 'Should contain enumerate')

        enumeration = gquery.get_enumeration(rq, 'o', 'http://mock-endpoint/sparql', metadata)
        self.assertIsInstance(enumeration, list, 'Should return a list of values')
        self.assertEqual(len(enumeration), 2, 'Should have two elements')

    def test_get_yaml_decorators(self):
        rq, _ = self.loader.getTextForName('test-sparql')

        decorators = gquery.get_yaml_decorators(rq)

        # Query always exist -- the rest must be present on the file.
        self.assertIn('query', decorators, 'Should have a query field')
        self.assertIn('summary', decorators, 'Should have a summary field')
        self.assertIn('pagination', decorators,
                      'Should have a pagination field')
        self.assertIn('enumerate', decorators, 'Should have a enumerate field')

        self.assertIsInstance(
            decorators['summary'], six.string_types, 'Summary should be text')
        self.assertIsInstance(
            decorators['pagination'], int, 'Pagination should be numeric')
        self.assertIsInstance(
            decorators['enumerate'], list, 'Enumerate should be a list')

    def test_get_json_decorators(self):
        rq, _ = self.loader.getTextForName('test-sparql-jsonconf')

        decorators = gquery.get_yaml_decorators(rq)

        # Query always exist -- the rest must be present on the file.
        self.assertIn('query', decorators, 'Should have a query field')
        self.assertIn('summary', decorators, 'Should have a summary field')
        self.assertIn('pagination', decorators,
                      'Should have a pagination field')
        self.assertIn('enumerate', decorators, 'Should have a enumerate field')

        self.assertIsInstance(
            decorators['summary'], six.string_types, 'Summary should be text')
        self.assertIsInstance(
            decorators['pagination'], int, 'Pagination should be numeric')
        self.assertIsInstance(
            decorators['enumerate'], list, 'Enumerate should be a list')

    def test_get_metadata(self):
        rq, _ = self.loader.getTextForName('test-sparql')

        metadata = gquery.get_metadata(rq, '')
        self.assertIn('type', metadata, 'Should have a type field')
        self.assertIn('variables', metadata, 'Should have a variables field')
        self.assertEqual(metadata['type'], 'SelectQuery',
                         'Should be type SelectQuery')
        self.assertIsInstance(
            metadata['variables'], list, 'Should be a list of variables')
        for var in metadata['variables']:
            self.assertIsInstance(var, rdflib.term.Variable,
                                  'Should be of type Variable')

    def test_paginate_query(self):
        rq, _ = self.loader.getTextForName('test-sparql')

        rq_pag = gquery.paginate_query(rq, 100, {})

        self.assertNotIn(
            'LIMIT', rq, 'Original query should not contain LIMIT keyword')
        self.assertIn('LIMIT', rq_pag,
                      'Paginated query should contain LIMIT keyword')
        self.assertNotIn(
            'OFFSET', rq, 'Original query should not contain OFFSET keyword')
        self.assertIn('OFFSET', rq_pag,
                      'Paginated query should contain OFFSET keyword')

    @staticmethod
    def build_get_parameter(origName, rwName):
        """Builds parameter description in the format returned by gquery.get_parameters"""
        return {
            'original': '?_{}'.format(origName),
            'name': rwName,
            'required': False,
            'enum': [],
            'type': 'literal',
            'datatype': 'xsd:string',
            'lang': 'en',
            'format': None
        }

    def test_rewrite_query(self):
        rq, _ = self.loader.getTextForName('test-rq')
        # Parameters on the format returned by gquery.get_parameters
        parameters = {
            'o1': self.build_get_parameter('o1', 'x1'),
            'o2': self.build_get_parameter('o2', 'x2'),
            'o3': self.build_get_parameter('o3', 'x3'),
            'o4': self.build_get_parameter('o4', 'x4'),
            'o5': self.build_get_parameter('o5', 'x5'),
            'o6': self.build_get_parameter('o6', 'x6'),
            'o7': self.build_get_parameter('o7', 'x7')
        }
        args = {
            'o1': 'x1',
            'o2': 'x2',
            'o3': 'x3',
            'o4': 'x4',
            'o5': 'x5',
            'o6': 'x6',
            'o7': 'x7'
        }
        # Rewritten query will probably be incorrect because parameters are not
        # carefully constructed, but that is not the scope of this test
        rq_rw = gquery.rewrite_query(rq, parameters, args)

        for pName, pValue in parameters.items():
            self.assertIn(
                pName, rq, 'Original query should contain original parameter name')
            self.assertNotIn(
                pName, rq_rw, 'Rewritten query should not contain original parameter name')
            self.assertNotIn(
                pValue['name'], rq, 'Original query should not contain replacement parameter value')
            self.assertIn(
                pValue['name'], rq_rw, 'Rewritten query should contain replacement parameter value')

    def test_sparql_transformer(self):
        rq, _ = self.loader.getTextForName('test-json')

        endpoint, _ = gquery.guess_endpoint_uri(rq, self.loader)
        self.assertEqual('http://dbpedia.org/sparql', endpoint, 'Should match endpoint in test-json.json')

        resp, status, headers = utils.dispatchSPARQLQuery(rq, self.loader, content=None, requestArgs={},
                                                          acceptHeader='application/json',
                                                          requestUrl='http://', formData={})
        self.assertEqual(status, 200)
        self.assertIsInstance(resp, list)
        self.assertIn('id', resp[0])


if __name__ == '__main__':
    unittest.main()
