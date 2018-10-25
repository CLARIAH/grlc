import re

def getSwaggerPaginationDef(resultsPerPage):
    '''Build swagger spec section for pagination'''
    return {
        "name":  "page",
        "type":  "int",
        "in":  "query",
        "description":  "The page number for this paginated query ({} results per page)".format(resultsPerPage)
    }

def buildPaginationHeader(resultCount, resultsPerPage, pageArg, url):
    '''Build link header for result pagination'''
    lastPage = resultCount / resultsPerPage

    if pageArg:
        page = int(pageArg)
        next_url = re.sub("page=[0-9]+", "page={}".format(page + 1), url)
        prev_url = re.sub("page=[0-9]+", "page={}".format(page - 1), url)
        first_url = re.sub("page=[0-9]+", "page=1", url)
        last_url = re.sub("page=[0-9]+", "page={}".format(lastPage), url)
    else:
        page = 1
        next_url = url + "?page=2"
        prev_url = ""
        first_url = url + "?page=1"
        last_url = url + "?page={}".format(lastPage)

    if page == 1:
        headerLink = "<{}>; rel=next, <{}>; rel=last".format(next_url, last_url)
    elif page == lastPage:
        headerLink = "<{}>; rel=prev, <{}>; rel=first".format(prev_url, first_url)
    else:
        headerLink = "<{}>; rel=next, <{}>; rel=prev, <{}>; rel=first, <{}>; rel=last".format(next_url, prev_url, first_url, last_url)
    return headerLink
