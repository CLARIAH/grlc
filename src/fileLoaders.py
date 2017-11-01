import static as static
import requests

from glob import glob

from queryTypes import qType

class BaseLoader:
    def getTextForName(self, query_name):
        # The URIs of all candidates
        rq_name = query_name + '.rq'
        sparql_name = query_name + '.sparql'
        tpf_name = query_name + '.tpf'
        candidates = [
            (rq_name, qType['SPARQL']),
            (sparql_name, qType['SPARQL']),
            (tpf_name, qType['TPF'])
        ]

        for queryFullName, queryType in candidates:
            queryText = self._getText(queryFullName)
            if queryText:
                return queryText, queryType
        # No query found...
        return '', None

class GithubLoader(BaseLoader):
    def __init__(self, user, repo, sha, prov):
        self.user = user
        self.repo = repo
        self.sha = sha
        self.prov = prov

    def fetchFiles(self):
        api_repo_content_uri = static.GITHUB_API_BASE_URL + self.user + '/' + self.repo + '/contents'
        params = {
            'ref' : 'master' if self.sha is None else self.sha
        }
        resp = requests.get(api_repo_content_uri, headers={'Authorization': 'token {}'.format(static.ACCESS_TOKEN)}, params=params).json()
        return resp

    def getRawRepoUri(self):
        raw_repo_uri = static.GITHUB_RAW_BASE_URL + self.user + '/' + self.repo
        if self.sha is None:
            raw_repo_uri += '/master/'
        else:
            raw_repo_uri += '/blob/{}/'.format(self.sha)
        return raw_repo_uri

    def getTextFor(self, fileItem):
        raw_query_uri = fileItem['download_url']
        resp = self._getText(raw_query_uri)

        # Add query URI as used entity by the logged activity
        self.prov.add_used_entity(raw_query_uri)
        return resp

    def _getText(self, query_name):
        query_uri = self.getRawRepoUri() + query_name
        req = requests.get(query_uri, headers={'Authorization': 'token {}'.format(static.ACCESS_TOKEN)})
        if req.status_code == 200:
            return req.text
        else:
            return None

class LocalLoader(BaseLoader):
    def __init__(self):
        self.baseDir = static.LOCAL_SPARQL_DIR

    def fetchFiles(self):
        files = glob(self.baseDir + '*')
        return [ { 'name': f.replace(self.baseDir, '') } for f in files ]

    def getRawRepoUri(self):
        return ''

    def _getText(self, query_name):
        f = open(self.baseDir + query_name, 'r')
        lines = f.readlines()
        text = ''.join(lines)
        return text

    def getTextFor(self, fileItem):
        return self._getText(fileItem['name'])
