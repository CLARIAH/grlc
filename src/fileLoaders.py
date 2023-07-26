# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

import grlc.static as static
from grlc.queryTypes import qType, guessQueryType
import grlc.glogging as glogging

import json
import gitlab
import requests
import yaml
import urllib.parse
import base64
import os
from os import path
from glob import glob
from github import Github
from github.GithubObject import NotSet
from github.GithubException import BadCredentialsException
from configparser import ConfigParser
from urllib.parse import urljoin

# util variables
glogger = glogging.getGrlcLogger(__name__)


class BaseLoader:
    """Base class for File Loaders"""
    def getTextForName(self, query_name):
        """Return the query text and query type for the given query name.
        Note that file extention is not part of the query name. For example,
        for `query_name='query1'` would return the content of file `query1.rq`
        from the loader's source (assuming such file exists)."""
        # The URIs of all candidates
        candidateNames = [
            query_name + '.rq',
            query_name + '.sparql',
            query_name + '.tpf',
            query_name + '.json'
        ]
        candidates = [
            (name, guessQueryType(name)) for name in candidateNames
        ]

        for queryFullName, queryType in candidates:
            queryText = self._getText(queryFullName)
            if queryText:
                if (queryType == qType['JSON']):
                    queryText = json.loads(queryText)
                    if 'proto' not in queryText and '@graph' not in queryText:
                        continue
                return queryText, queryType
        # No query found...
        return '', None

    def _getText(self, queryFullName):
        """To be implemented by sub-classes"""
        raise NotImplementedError("Subclasses must override _getText()!")

    def fetchFiles(self):
        """To be implemented by sub-classes"""
        raise NotImplementedError("Subclasses must override fetchFiles()!")


class GithubLoader(BaseLoader):
    """Github based File Loader. Retrieves information from specified Github
    repository to construct a grlc specification."""

    def __init__(self, user, repo, subdir=None, sha=None, prov=None):
        """Create a new GithubLoader.

        Keyword arguments:
        user -- Github user name of the target github repo.
        repo -- Repository name of the target github repo.
        subdir -- Target subdirectory within the given repo. (default: None).
        sha -- Github commit identifier hash (default: None).
        prov -- grlcPROV object for tracking provenance (default: None)."""
        self.user = user
        self.repo = repo
        self.subdir = (subdir + "/") if subdir else ""
        self.sha = sha if sha else NotSet
        self.prov = prov
        gh = Github(static.ACCESS_TOKEN)
        try:
            self.gh_repo = gh.get_repo(user + '/' + repo, lazy=False)
        except BadCredentialsException:
            raise Exception('BadCredentials: have you set up github_access_token on config.ini ?')
        except Exception:
            raise Exception('Repo not found: ' + user + '/' + repo)

    def fetchFiles(self):
        """Returns a list of file items contained on the github repo."""
        contents = self.gh_repo.get_contents(self.subdir.strip('/'), ref=self.sha)
        files = []
        for content_file in contents:
            if content_file.type == 'file':
                files.append({
                        'download_url': content_file.download_url,
                        'name': content_file.name,
                        'decoded_content': content_file.decoded_content
                    })
        return files

    def getRawRepoUri(self):
        """Returns the root url of the github repo."""
        # TODO: replace by gh_repo.html_url ?
        raw_repo_uri = static.GITHUB_RAW_BASE_URL + self.user + '/' + self.repo
        if self.sha is NotSet:
            raw_repo_uri += '/master/'
        else:
            raw_repo_uri += '/{}/'.format(self.sha)
        return raw_repo_uri

    def getTextFor(self, fileItem):
        """Returns the contents of the given file item on the github repo."""
        raw_query_uri = fileItem['download_url']

        # Add query URI as used entity by the logged activity
        if self.prov is not None:
            self.prov.add_used_entity(raw_query_uri)
        return str(fileItem['decoded_content'], 'utf-8')

    def _getText(self, query_name):
        """Return the content of the specified file contained in the github repo."""
        try:
            c = self.gh_repo.get_contents(self.subdir + query_name)
            return str(c.decoded_content, 'utf-8')
        except:
            return None

    def getRepoTitle(self):
        """Return the title of the github repo."""
        return self.gh_repo.name

    def getContactName(self):
        """Return the name of the owner of the github repo."""
        return self.gh_repo.owner.login

    def getContactUrl(self):
        """Return the home page of the owner of the github repo."""
        return self.gh_repo.owner.html_url

    def getCommitList(self):
        """Return a list of commits on the github repo."""
        return [c.sha for c in self.gh_repo.get_commits()]

    def getFullName(self):
        """Return the full name of the github repo (user/repo)."""
        return self.gh_repo.full_name

    def getRepoURI(self):
        """Return the full URI of the github repo."""
        return static.GITHUB_API_BASE_URL + self.gh_repo.full_name

    def getEndpointText(self):
        """Return content of endpoint file (endpoint.txt)"""
        return self._getText('endpoint.txt')

    def getLicenceURL(self):
        """Returns the URL of the license file in this repository if one exists."""
        for f in self.fetchFiles():
            if f['name'].lower() == 'license' or f['name'].lower() == 'licence':
                return f['download_url']
        return None

    def getRepoDescription(self):
        """Return the description of the repository"""
        return self.gh_repo.description


class GitlabLoader(BaseLoader):

    def __init__(self, user, repo, subdir=None, sha=None, prov=None, branch='main'):
        """Create a new GithubLoader.
        # TODO: Update to GITLAB !

        Keyword arguments:
        user -- Github user name of the target github repo.
        repo -- Repository name of the target github repo.
        subdir -- Target subdirectory within the given repo. (default: None).
        branch -- Branch
        sha -- Github commit identifier hash (default: None).
        prov -- grlcPROV object for tracking provenance (default: None)."""
        self.user = user
        self.repo = repo
        self.subdir = (subdir + "/") if subdir else ""
        self.branch = branch
        self.sha = sha if sha else None
        self.prov = prov
        gl = gitlab.Gitlab(
            url=static.GITLAB_URL, 
            private_token=static.ACCESS_TOKEN
        )
        try:
            self.gl_repo = gl.projects.get(user + '/' + repo)
        except BadCredentialsException:
            raise Exception('BadCredentials: have you set up github_access_token on config.ini ?')
        except Exception:
            raise Exception('Repo not found: ' + user + '/' + repo)

    def fetchFiles(self):
        """Returns a list of file items contained on the github repo."""
        gitlab_files = self.gl_repo.repository_tree(path=self.subdir.strip('/'), ref=self.branch, all=True)
        files = []
        for gitlab_file in gitlab_files:            
            if gitlab_file['type'] == 'blob':
                name = gitlab_file['name']
                files.append({
                    'download_url': path.join(self.getRawRepoUri(), self.subdir, name),
                    'name': name,
                    'decoded_content': str.encode(self._getText(gitlab_file['name']))
                })
        return files

    def getRawRepoUri(self):
        """Returns the root url of the github repo."""
        # TODO: replace by gh_repo.html_url ?
        return path.join(static.GITLAB_URL, self.user, self.repo, '-', 'raw', self.branch)

    def getTextFor(self, fileItem):
        """Returns the contents of the given file item on the github repo."""
        raw_query_uri = fileItem['download_url']

        # Add query URI as used entity by the logged activity
        if self.prov is not None:
            self.prov.add_used_entity(raw_query_uri)
        return str(fileItem['decoded_content'], 'utf-8')  

    def _getText(self, query_name):
        """Return the content of the specified file contained in the github repo."""
        try:
            file_path = path.join(self.subdir, query_name)
            f = self.gl_repo.files.get(file_path=file_path, ref=self.branch)
            file_content = base64.b64decode(f.content).decode("utf-8")
            return file_content.replace('\\n', '\n').replace('\\t', '\t')
        except:
            return None
    
    def getRepoTitle(self):
        """Return the title of the github repo."""
        return self.gl_repo.name

    def getContactName(self):
        """Return the name of the owner of the gitlab repo."""
        return self.gl_repo.namespace['name']

    def getContactUrl(self):
        """Return the home page of the owner of the gitlab repo."""
        return self.gl_repo.namespace['web_url']

    def getCommitList(self):
        """Return a list of commits on the gitlab repo."""
        return [ c.id for c in self.gl_repo.commits.list() ]

    def getFullName(self):
        """Return the full name of the gitlab repo (user/repo)."""
        return self.gl_repo.path_with_namespace

    def getRepoURI(self):
        """Return the full URI of the gitlab repo."""
        return self.gl_repo.web_url

    def getEndpointText(self):
        """Return content of endpoint file (endpoint.txt)"""
        return self._getText('endpoint.txt')

    def getLicenceURL(self):
        """Returns the URL of the license file in this repository if one exists."""
        for f in self.fetchFiles():
            if f['name'].lower() == 'license' or f['name'].lower() == 'licence':
                return f['download_url']
        return None

    def getRepoDescription(self):
        """Return the description of the repository"""
        return self.gl_repo.description



class LocalLoader(BaseLoader):
    """Local file system file loader. Retrieves information to construct
    a grlc specification from a local folder."""

    def __init__(self, baseDir=static.LOCAL_SPARQL_DIR):
        """Create a new LocalLoader.

        Keyword arguments:
        baseDir -- Local file system path where files are loaded from."""
        self.baseDir = baseDir

        config_fallbacks = {
            'repo_title': 'local',
            'api_description': 'API generated from local files',
            'contact_name': '',
            'contact_url': '',
            'licence_url': ''
        }
        config = ConfigParser(config_fallbacks)
        config.add_section('repo_info')
        config_filename = path.join(baseDir, 'local-api-config.ini')
        config.read(config_filename)
        self.repo_title = config.get('repo_info', 'repo_title')
        self.api_description = config.get('repo_info', 'api_description')
        self.contact_name = config.get('repo_info', 'contact_name')
        self.contact_url = config.get('repo_info', 'contact_url')
        self.licence_url = config.get('repo_info', 'licence_url')

    def fetchFiles(self):
        """Returns a list of file items contained on the local repo."""
        files = glob(path.join(self.baseDir, '*'))
        filesDef = []
        baseDirSlash = path.join(self.baseDir, '')
        for f in files:
            relative = f.replace(baseDirSlash, '')
            filesDef.append({
                'download_url': relative,
                'name': relative
            })
        return filesDef

    def getRawRepoUri(self):
        """Returns the root url of the local repo."""
        # Maybe return something like 'file:///path/to/local/queries' ?
        return ''

    def getTextFor(self, fileItem):
        """Returns the contents of the given file item on the local repo."""
        return self._getText(fileItem['download_url'])

    def _getText(self, filename):
        """Return the content of the specified file contained in the local repo."""
        targetFile = path.join(self.baseDir, filename)
        if path.exists(targetFile):
            with open(targetFile, 'r') as f:
                lines = f.readlines()
                text = ''.join(lines)
                return text
        else:
            return None

    def getRepoTitle(self):
        """Return the title of the local repo."""
        return self.repo_title

    def getContactName(self):
        """Return the name of the owner of the local repo."""
        return self.contact_name

    def getContactUrl(self):
        """Return the home page of the owner of the local repo."""
        return self.contact_url

    def getCommitList(self):
        """Return a list of commits (always a single commit) on the local repo."""
        return ['local']

    def getFullName(self):
        """Return the user/repo equivalent for the local repo."""
        return 'local/'

    def getRepoURI(self):
        """Return the full URI of the local repo."""
        return 'local-file-system'

    def getEndpointText(self):
        """Return content of endpoint file (endpoint.txt)"""
        return self._getText('endpoint.txt')

    def getLicenceURL(self):
        return self.licence_url

    def getRepoDescription(self):
        """Return the description of the API generated by local repository"""
        return self.api_description


class URLLoader(BaseLoader):
    """URL specification loader. Retrieves information to construct a grlc
    specification from a specification YAML file located on a remote server."""

    def __init__(self, spec_url):
        """Create a new URLLoader.

        Keyword arguments:
        spec_url -- URL where the specification YAML file is located."""
        headers = {'Accept' : 'text/yaml'}
        resp = requests.get(spec_url, headers=headers)
        if resp.status_code == 200:
            self.spec = yaml.load(resp.text)
            self.spec['url'] = spec_url
            self.spec['files'] = {}

            for query in self.spec['queries']:
                queryName, queryUrl = self.extractQueryInfo(query)

                item = {
                    'name': queryName,
                    'download_url': queryUrl
                }
                self.spec['files'][queryName] = item
            del self.spec['queries']
        else:
            raise Exception(resp.text)

    def extractQueryInfo(self, query):
        """Extract query name and URL from specification. These could 
        either be explicitly declared (values in a dict) or need to be 
        infered from the URL (which itself could be explicilty declared or 
        be the only element of query."""
        queryUrl = query['url'] if type(query) is dict else query

        if type(query) is dict and 'name' in query:
            queryName = query['name']
        else:
            queryNameExt = path.basename(queryUrl)
            queryName = path.splitext(queryNameExt)[0] # Remove extention
        return queryName, queryUrl

    def fetchFiles(self):
        """Returns a list of file items contained on specification."""
        files = [
            v for k,v in self.spec['files'].items()
        ]
        return files

    def getRawRepoUri(self):
        """Returns the root url of the specification."""
        return self.spec['url']

    def getTextFor(self, fileItem):
        """Returns the contents of the given file item on the specification."""
        # TODO: tiene sentido esto? O es un hack horrible ?
        nameExt = path.basename(fileItem['download_url'])
        return self._getText(fileItem['name'])

    def getTextForName(self, query_name):
        """Return the query text and query type for the given query name.
        Specific implementation for URLLoader."""
        try:
            queryText = self._getText(query_name)
            queryType = guessQueryType(self.spec['files'][query_name]['download_url'])
            return queryText, queryType
        except Exception as e:
            # No query found...
            return '', None

    def _getText(self, itemName):
        """Return the content of the specified item in the specification."""
        if itemName in self.spec['files']:
            headers = {'Accept' : 'text/plain'}
            itemUrl = self.spec['files'][itemName]['download_url']
            itemUrl = urljoin(self.spec['url'], itemUrl) # Join with base URL if relative URL
            resp = requests.get(itemUrl, headers=headers)
            if resp.status_code == 200:
                return resp.text
            else:
                raise Exception('HTTP status {} encountered while loading {}'.format(resp.status_code, itemUrl))
        else:
            return None

    def getRepoTitle(self):
        """Return the title contained on the specification."""
        return self.spec['title']

    def getContactName(self):
        """Return the name of the contact person for the specification."""
        return self.spec['contact']['name'] if self.spec['contact']['name'] else ''

    def getContactUrl(self):
        """Return the home page defined in the specification."""
        return self.spec['contact']['url'] if self.spec['contact']['url'] else ''

    def getCommitList(self):
        """Return a list of commits (always a single commit) for the specification."""
        return ['param']

    def getFullName(self):
        """Return the user/repo equivalent for the specification."""
        return self.getContactName()

    def getRepoURI(self):
        """Return the full URI of the specification."""
        return self.getRawRepoUri()

    def getLicenceURL(self):
        """Returns the URL of the license file in the specification."""
        return self.spec['licence'] if 'licence' in self.spec else None

    def getEndpointText(self):
        """Return content of endpoint file (endpoint.txt)"""
        return "" #TODO: add endpoint to spec file definition

    def getRepoDescription(self):
        """Return the description of the repository"""
        if 'description' in self.spec:
            return self.spec['description']
        else:
            return 'API definition loaded from ' + self.getRawRepoUri()

