import re
from flask import request

def getSwaggerPaginationDef(resultsPerPage):
    return {
        "name":  "page",
        "type":  "int",
        "in":  "query",
        "description":  "The page number for this paginated query ({} results per page)".format(resultsPerPage)
    }

def buildPaginationHeader(resultCount, resultsPerPage):
    lastPage = resultCount / resultsPerPage
    if 'page' in request.args:
        page = int(request.args['page'])
        next_url = re.sub("page=[0-9]+", "page={}".format(page + 1), request.url)
        prev_url = re.sub("page=[0-9]+", "page={}".format(page - 1), request.url)
        first_url = re.sub("page=[0-9]+", "page=1", request.url)
        last_url = re.sub("page=[0-9]+", "page={}".format(lastPage), request.url)
    else:
        page = 1
        next_url = request.url + "?page={}".format(page + 1)
        prev_url = request.url + "?page={}".format(page - 1)
        first_url = request.url + "?page={}".format(page)
        last_url = request.url + "?page={}".format(lastPage)

    if page == 1:
        headerLink = "<{}>; rel=next, <{}>; rel=last".format(next_url, last_url)
    elif page == lastPage:
        headerLink = "<{}>; rel=prev, <{}>; rel=first".format(prev_url, first_url)
    else:
        headerLink = "<{}>; rel=next, <{}>; rel=prev, <{}>; rel=first, <{}>; rel=last".format(next_url, prev_url, first_url, last_url)
    return headerLink
