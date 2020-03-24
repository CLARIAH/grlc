import grlc.static as static
from grlc.queryTypes import qType

import json
import requests
import yaml
from os import path
from glob import glob
from github import Github
from github.GithubException import BadCredentialsException


class BaseLoader:
    """Base class for File Loaders"""
    def getTextForName(self, query_name):
        """Return the query text and query type for the given query name.
        Note that file extention is not part of the query name. For example,
        for `query_name='query1'` would return the content of file `query1.rq`
        from the loader's source (assuming such file exists)."""
        # The URIs of all candidates
        rq_name = query_name + '.rq'
        sparql_name = query_name + '.sparql'
        tpf_name = query_name + '.tpf'
        json_name = query_name + '.json'
        candidates = [
            (rq_name, qType['SPARQL']),
            (sparql_name, qType['SPARQL']),
            (tpf_name, qType['TPF']),
            (json_name, qType['JSON'])
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

    def getLicenceURL(self):
        """Returns the URL of the license file in this repository if one exists."""
        for f in self.fetchFiles():
            if f['name'].lower() == 'license' or f['name'].lower() == 'licence':
                return f['download_url']
        return None

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
        self.subdir = subdir
        self.sha = sha
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
        api_repo_content_uri = static.GITHUB_API_BASE_URL + self.user + '/' + self.repo + '/contents'
        if self.subdir:
            api_repo_content_uri += '/' + str(self.subdir)
        params = {
            'ref': 'master' if self.sha is None else self.sha
        }
        # TODO: use Github instead of requests ?
        resp = requests.get(api_repo_content_uri, headers={'Authorization': 'token {}'.format(static.ACCESS_TOKEN)},
                            params=params)
        if resp.ok:
            return resp.json()
        else:
            raise Exception(resp.text)

    def getRawRepoUri(self):
        """Returns the root url of the github repo."""
        raw_repo_uri = static.GITHUB_RAW_BASE_URL + self.user + '/' + self.repo
        if self.sha is None:
            raw_repo_uri += '/master/'
        else:
            raw_repo_uri += '/{}/'.format(self.sha)
        return raw_repo_uri

    def getTextFor(self, fileItem):
        """Returns the contents of the given file item on the github repo."""
        raw_query_uri = fileItem['download_url']
        if '/' in raw_query_uri:
            raw_query_uri = raw_query_uri.split('/')[-1]
        resp = self._getText(raw_query_uri)

        # Add query URI as used entity by the logged activity
        if self.prov is not None:
            self.prov.add_used_entity(raw_query_uri)
        return resp

    def _getText(self, query_name):
        """Return the content of the specified file contained in the github repo."""
        query_uri = self.getRawRepoUri() + query_name
        if self.subdir:
            query_uri = self.getRawRepoUri() + self.subdir + '/' + query_name
        print("Requesting query at " + str(query_uri))
        req = requests.get(query_uri, headers={'Authorization': 'token {}'.format(static.ACCESS_TOKEN)})
        if req.status_code == 200:
            return req.text
        else:
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


class LocalLoader(BaseLoader):
    """Local file system file loader. Retrieves information to construct 
    a grlc specification from a local folder."""

    def __init__(self, baseDir=static.LOCAL_SPARQL_DIR):
        """Create a new LocalLoader.

        Keyword arguments:
        baseDir -- Local file system path where files are loaded from."""
        self.baseDir = baseDir

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
        return 'local'

    def getContactName(self):
        """Return the name of the owner of the local repo."""
        return ''

    def getContactUrl(self):
        """Return the home page of the owner of the local repo."""
        return ''

    def getCommitList(self):
        """Return a list of commits (always a single commit) on the local repo."""
        return ['local']

    def getFullName(self):
        """Return the user/repo equivalent for the local repo."""
        return 'local/'

    def getRepoURI(self):
        """Return the full URI of the local repo."""
        return 'local-file-system'


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
            for queryUrl in self.spec['queries']:
                queryNameExt = path.basename(queryUrl)
                queryName = path.splitext(queryNameExt)[0] # Remove extention
                item = {
                    'name': queryName,
                    'download_url': queryUrl
                }
                self.spec['files'][queryNameExt] = item
            del self.spec['queries']
        else:
            raise Exception(resp.text)


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
        return self._getText(nameExt)

    def _getText(self, itemName):
        """Return the content of the specified item in the specification."""
        if itemName in self.spec['files']:
            itemUrl = self.spec['files'][itemName]['download_url']
            headers = {'Accept' : 'text/plain'}
            resp = requests.get(itemUrl, headers=headers)
            if resp.status_code == 200:
                return resp.text
            else:
                raise Exception(resp.text)
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
        return self.spec['licence'] if self.spec['licence'] else ''
