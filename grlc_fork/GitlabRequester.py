# /*
# * SPDX-License-Identifier: MIT
# * SPDX-FileCopyrightText: Copyright (c) 2022 Orange SA
# *
# * Author: Mihary RANAIVOSON
# * Modifications: 
# *     - This file isn't necessary for making work GRLC.
# *     - This class just permits to manipulate HTTP query created by GRLC.
# *     - It would be nice if there were also FileRequester, URLRequester and GithubRequester classes
# */


import gitlab
import urllib.parse
import requests
import base64
import yaml
import os




class GitlabRequester:

    def __init__(self, grlc_url, endpoint_url, gitlab_url, user, repo, token, branch='main', subdir=None):
        self.grlc_url = grlc_url
        self.endpoint_url = endpoint_url
        self.gitlab_url = gitlab_url
        self.user = user
        self.repo = repo
        self.token = token
        self.branch = branch
        self.subdir = subdir
        
        self.gl = gitlab.Gitlab(
            url=self.gitlab_url, 
            private_token=self.token
        )
        self.gl_repo = self.gl.projects.get(self.user + '/' + self.repo)
        self.gl_files = self.gl_repo.repository_tree(
            path=self.subdir.strip('/'), 
            ref=self.branch, 
            all=True
        )

        self.has_subdir = False
        if (self.subdir != None) and (self.subdir != "") and (self.subdir != "."):
            self.has_subdir = True

        self.accepted_response_type = [ "text/csv", "application/json", "text/html" ]



    def execute_query(self, filename, response_type="text/csv"):
        '''
        Call the http query which executes the SPARQL query
        '''
        http_query_url = self.get_http_query_url(filename)
        http_method = self.get_http_method(self.get_content_file(filename))
        response_type = response_type if response_type in self.accepted_response_type else self.accepted_response_type[0]
        headers = { "Accept": response_type }
        if http_method == "GET":
            return requests.get(url=http_query_url, headers=headers)
        else:
            return requests.post(url=http_query_url, headers=headers)



    def get_curl_query(self, filename, response_type="text/csv"):
        '''
        From a filename, return the curl command for executing the spaql query (contained in the file)
        '''
        http_query_url = self.get_http_query_url(filename)
        raw_query = self.get_content_file(filename)
        method = self.get_http_method(raw_query)
        response_type = response_type if response_type in self.accepted_response_type else self.accepted_response_type[0]
        return f'''curl -X {method} "{http_query_url}" -H "accept: {response_type}"'''



    def get_http_query_url(self, filename):
        '''
        From a filename, return the http url which execute this query
        '''
        if self.has_subdir:
            begin_url = f"{self.grlc_url}/api-gitlab/{self.user}/{self.repo}/query/branch/{self.branch}/subdir/{self.subdir}"
        else:
            begin_url = f"{self.grlc_url}/api-gitlab/{self.user}/{self.repo}/query/branch/{self.branch}"
        middle_url = self.get_query_name(filename)
        end_url = "endpoint=" + urllib.parse.quote(self.endpoint_url, safe='')
        return begin_url + "/" + middle_url + "?" + end_url



    def get_content_file(self, filename):
        '''
        From a filename, return the content of the file
        '''
        try:
            file_path = os.path.join(self.subdir, filename)
            f = self.gl_repo.files.get(file_path=file_path, ref=self.branch)
            file_content = base64.b64decode(f.content).decode("utf-8")
            return file_content.replace('\\n', '\n').replace('\\t', '\t')
        except:
            return None  



    def get_http_method(self, raw_query):
        '''
        From the content of a SPARQL query, return the http method to use
        '''
        yaml_string = "\n".join([row.lstrip('#+') for row in raw_query.split('\n') if row.startswith('#+')])
        query_string = "\n".join([row for row in raw_query.split('\n') if not row.startswith('#+')])
        query_metadata = yaml.unsafe_load(yaml_string)
        if 'method' in query_metadata:
            return query_metadata['method']
        else:
            return "POST"



    def get_query_name(self, filename):
        '''
        Get the name of the SPARQL query
        '''
        query_name = filename[:-len(".rq")] if filename.endswith(".rq") else filename
        return query_name[:-len(".sparql")] if filename.endswith(".sparql") else query_name



    def get_filenames(self):
        '''
        Get the names of the files which contains sparql queries
        Search only in the branch (self.branch) and in the directory (self.subdir)
        '''
        filenames = []

        for file0 in self.gl_files:            
            filename = file0['name']
            if file0['type'] == 'blob':
                if filename.endswith(".rq") or filename.endswith(".sparql"):
                    filenames.append(filename)
        
        return filenames
    
