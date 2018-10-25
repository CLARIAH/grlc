import static
from github import Github

def get_blank_spec():
    swag = {}
    swag['swagger'] = '2.0'
    swag['schemes'] = [] # 'http' or 'https' -- leave blank to make it dependent on how UI is loaded
    swag['paths'] = {}
    swag['definitions'] = {
        'Message': {'type': 'string'}
    }
    return swag

def get_path_for_item(item):
    item_path = {
        item['method']: {
            "tags" : item['tags'],
            "summary" : item['summary'],
            "description" : item['description'] + "\n\n```{}```".format(item['query']),
            "produces" : ["text/csv", "application/json", "text/html"],
            "parameters": item['params'] if 'params' in item else None,
            "responses": {
                "200" : {
                    "description" : "Query response",
                    "schema" : {
                        "type" : "array",
                        "items": {
                            "type": "object",
                            "properties": item['item_properties'] if 'item_properties' in item else None
                        },
                    }
                },
                "default" : {
                    "description" : "Unexpected error",
                    "schema" : {
                        "$ref" : "#/definitions/Message"
                    }
                }
            }
        }
    }
    return item_path

def get_repo_info(user, repo, sha, prov_g):
    if user and repo:
        user_repo = user + '/' + repo
        api_repo_uri = static.GITHUB_API_BASE_URL + user_repo

        # Init provenance recording
        gh = Github(static.ACCESS_TOKEN)
        gh_repo = gh.get_repo(user + '/' + repo)

        repo_title = gh_repo.name
        contact_name = gh_repo.owner.login
        contact_url = gh_repo.owner.html_url

        # Add the API URI as a used entity by the activity
        if prov_g:
            prov_g.add_used_entity(api_repo_uri)

        commit_list = [ c.sha for c in gh_repo.get_commits() ]

        prev_commit = None
        next_commit = None

        version = sha
        if sha is None:
            version = commit_list[0]

        if commit_list.index(version) < len(commit_list) - 1:
            prev_commit = commit_list[commit_list.index(version)+1]
        if commit_list.index(version) > 0:
            next_commit = commit_list[commit_list.index(version)-1]
    else:
        user_repo = 'local/local'
        prev_commit = []
        next_commit = []
        version = 'local'
        repo_title = 'local'
        contact_name = ''
        contact_url = ''
        prov_g = None

    info = {
        'version': version,
        'title': repo_title,
        'contact': {
            'name': contact_name,
            'url': contact_url
        },
        'license': {
            'name' : 'License',
            'url': static.GITHUB_RAW_BASE_URL + user_repo + '/master/LICENSE'
        }
    }

    basePath = '/api/' + user_repo + '/'
    if sha is not None:
        basePath = '/api/' + user_repo + '/commit/' + sha + '/'


    prev_commit, next_commit, info, basePath = 1,2,3,4
    return prev_commit, next_commit, info, basePath
