# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

import pytest
from mock import patch
from tests.mock_data import mockLoader, mock_requestsUrl
from grlc.server import app

@pytest.fixture(scope='class')
def client(request):
    '''Build http client'''
    with app.test_client() as client:
        yield client

class TestGrlcHome:
    '''Test all grlc server endpoints.'''

    def test_home(self, client):
        """Testing get from grlc home page"""
        rv = client.get('/')
        assert rv.status_code == 200
        assert 'text/html' in rv.content_type
        body = str(object=rv.data, encoding=rv.charset, errors='strict')
        assert '<title>grlc</title>' in body
        assert 'grlc generates RESTful APIs using SPARQL queries stored in GitHub repositories' in body

class TestGrlcFrontEnd:
    '''Test all grlc api front end generation (swagger html page).'''

    def validate(self, response):
        assert response.status_code == 200
        assert 'text/html' in response.content_type
        body = str(object=response.data, encoding=response.charset, errors='strict')
        assert '<div id="swagger-ui"></div>' in body

    def test_repo(self, client):
        """..."""
        rv = client.get('/api-git/testuser/testrepo')
        self.validate(rv)

    def test_subdir(self, client):
        """..."""
        rv = client.get('/api-git/testuser/testrepo/subdir/<subdir>')
        self.validate(rv)

    def test_commit(self, client):
        """..."""
        rv = client.get('/api-git/testuser/testrepo/commit/<sha>')
        self.validate(rv)

    def test_subdir_commit(self, client):
        """..."""
        rv = client.get('/api-git/testuser/testrepo/subdir/<subdir>/commit/<sha>')
        self.validate(rv)

    def test_local(self, client):
        """..."""
        rv = client.get('/api-local/')
        self.validate(rv)

    def test_url(self, client):
        """..."""
        rv = client.get('/api-url/?specUrl=<specUrl>')
        self.validate(rv)

class TestGrlcSpec:
    '''Test all grlc api spec generation.'''

    def validate(self, response):
        assert response.status_code == 200
        assert 'application/json' in response.content_type
        spec = response.json
        assert spec['swagger'] == '2.0'
        assert 'paths' in spec
        assert spec['info']['title'] != 'ERROR!'

    @patch('grlc.utils.getLoader')
    def test_repo(self, mock_loader, client):
        """..."""
        mock_loader.return_value = mockLoader

        rv = client.get('/api-git/testuser/testrepo/swagger')
        self.validate(rv)

    @patch('grlc.utils.getLoader')
    def test_subdir(self, mock_loader, client):
        """..."""
        mock_loader.return_value = mockLoader

        rv = client.get('/api-git/testuser/testrepo/subdir/testsubdir/swagger')
        self.validate(rv)

    @patch('grlc.utils.getLoader')
    def test_commit(self, mock_loader, client):
        """..."""
        mock_loader.return_value = mockLoader

        rv = client.get('/api-git/testuser/testrepo/commit/local/swagger')
        self.validate(rv)

    @patch('grlc.utils.getLoader')
    def test_subdir_commit(self, mock_loader, client):
        """..."""
        mock_loader.return_value = mockLoader

        rv = client.get('/api-git/testuser/testrepo/subdir/testsubdir/commit/local/swagger')
        self.validate(rv)

    def test_local(self, client):
        """..."""
        rv = client.get('/api-local/swagger')
        self.validate(rv)

    @patch('requests.get', side_effect=mock_requestsUrl)
    def test_url(self, mock_get, client):
        """..."""
        rv = client.get('/api-url/swagger?specUrl=http://example.org/url.yml')
        self.validate(rv)

class TestGrlcExec:
    '''Test all grlc api execution endpoints.'''

    @classmethod
    def setup_class(self):
        query_response = [{ "result": "mock" }]
        status = 200
        headers = { 'Content-Type': 'application/json' }
        self.mock_response = query_response, status, headers

    def validate(self, response):
        assert response.status_code == 200
        assert 'application/json' in response.content_type
        assert len(response.json) > 0
        assert 'result' in response.json[0]
        assert response.json[0]['result'] == 'mock'

    @patch('grlc.utils.getLoader')
    @patch('grlc.utils.dispatch_query')
    def test_repo(self, mock_dispatch, mock_loader, client):
        """..."""
        mock_dispatch.return_value = self.mock_response
        rv = client.get('/api-git/testuser/testrepo/query_name',
            headers={'Accept': 'application/json'})
        self.validate(rv)

    @patch('grlc.utils.getLoader')
    @patch('grlc.utils.dispatch_query')
    def test_subdir(self, mock_dispatch, mock_loader, client):
        """..."""
        mock_dispatch.return_value = self.mock_response

        # Check types of data passed to make_response.
        # If jsonify(dict) fixes the issue, patch make_response to jsonify(query_response) before 
        # returning data to rv.
        rv = client.get('/api-git/testuser/testrepo/subdir/testsubdir/query_name',
            headers={'accept': 'application/json'})
        self.validate(rv)

    @patch('grlc.utils.getLoader')
    @patch('grlc.utils.dispatch_query')
    def test_commit(self, mock_dispatch, mock_loader, client):
        """..."""
        mock_dispatch.return_value = self.mock_response

        rv = client.get('/api-git/testuser/testrepo/commit/local/query_name',
            headers={'accept': 'application/json'})
        self.validate(rv)

    @patch('grlc.utils.getLoader')
    @patch('grlc.utils.dispatch_query')
    def test_subdir_commit(self, mock_dispatch, mock_loader, client):
        """..."""
        mock_dispatch.return_value = self.mock_response

        rv = client.get('/api-git/testuser/testrepo/subdir/testsubdir/commit/local/query_name',
            headers={'accept': 'application/json'})
        self.validate(rv)

    @patch('grlc.utils.dispatch_query')
    def test_local(self, mock_dispatch, client):
        """..."""
        mock_dispatch.return_value = self.mock_response

        rv = client.get('/api-local/query_name',
            headers={'accept': 'application/json'})
        self.validate(rv)

    @patch('requests.get', side_effect=mock_requestsUrl)
    @patch('grlc.utils.dispatch_query')
    def test_url(self, mock_dispatch, mock_get, client):
        """..."""
        mock_dispatch.return_value = self.mock_response

        rv = client.get('/api-url/<query_name>?specUrl=http://example.org/url.yml',
            headers={'accept': 'application/json'})
        self.validate(rv)
