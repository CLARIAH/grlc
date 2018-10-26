import utils

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
            'tags' : item['tags'],
            'summary' : item['summary'],
            'description' : item['description'] + '\n\n```{}```'.format(item['query']),
            'produces' : ['text/csv', 'application/json', 'text/html'],
            'parameters': item['params'] if 'params' in item else None,
            'responses': {
                '200' : {
                    'description' : 'Query response',
                    'schema' : {
                        'type' : 'array',
                        'items': {
                            'type': 'object',
                            'properties': item['item_properties'] if 'item_properties' in item else None
                        },
                    }
                },
                'default' : {
                    'description' : 'Unexpected error',
                    'schema' : {
                        '$ref' : '#/definitions/Message'
                    }
                }
            }
        }
    }
    return item_path

def get_repo_info(user, repo, sha, prov_g):
    loader = utils.getLoader(user, repo, sha, prov_g)

    user_repo = loader.getFullName()
    repo_title = loader.getRepoTitle()
    contact_name = loader.getContactName()
    contact_url = loader.getContactUrl()
    commit_list = loader.getCommitList()
    licence_url = loader.getLicenceURL()

    # Add the API URI as a used entity by the activity
    if prov_g:
        prov_g.add_used_entity(loader.getRepoURI())

    prev_commit = None
    next_commit = None
    version = sha if sha else commit_list[0]
    if commit_list.index(version) < len(commit_list) - 1:
        prev_commit = commit_list[commit_list.index(version)+1]
    if commit_list.index(version) > 0:
        next_commit = commit_list[commit_list.index(version)-1]

    info = {
        'version': version,
        'title': repo_title,
        'contact': {
            'name': contact_name,
            'url': contact_url
        },
        'license': {
            'name' : 'License',
            'url': licence_url
        }
    }

    basePath = '/api/' + user_repo + '/'
    basePath += ('commit/' + sha + '/') if sha else ''

    return prev_commit, next_commit, info, basePath
