# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode, ParseResult

def getSwaggerPaginationDef(resultsPerPage):
    """Build swagger spec section for pagination"""
    return {
        "name":  "page",
        "type":  "int",
        "in":  "query",
        "description":  "The page number for this paginated query ({} results per page)".format(resultsPerPage)
    }

def buildPaginationHeader(resultCount, resultsPerPage, pageArg, url):
    """Build link header for result pagination"""
    lastPage = resultCount / resultsPerPage

    url_parts = urlparse(url)
    query = dict(parse_qsl(url_parts.query)) # Use dict parse_qsl instead of parse_qs to ensure 'page' is unique

    first_url = _buildNewUrlWithPage(url_parts, query, page=1)
    last_url = _buildNewUrlWithPage(url_parts, query, page=lastPage)

    if not pageArg:
        next_url = _buildNewUrlWithPage(url_parts, query, page=1)
        prev_url = ""
        headerLink = "<{}>; rel=next, <{}>; rel=last".format(next_url, last_url)
    else:
        page = int(pageArg)
        next_url = _buildNewUrlWithPage(url_parts, query, page + 1)
        prev_url = _buildNewUrlWithPage(url_parts, query, page - 1)

        if page == lastPage:
            headerLink = "<{}>; rel=prev, <{}>; rel=first".format(prev_url, first_url)
        else:
            headerLink = "<{}>; rel=next, <{}>; rel=prev, <{}>; rel=first, <{}>; rel=last".format(next_url, prev_url, first_url, last_url)
    return headerLink

def _buildNewUrlWithPage(url_parts, query, page):
    query['page'] = page
    new_query = urlencode(query)
    newParsedUrl = ParseResult(scheme=url_parts.scheme, netloc=url_parts.netloc, path=url_parts.path,
                               params=url_parts.params, query=new_query, fragment=url_parts.fragment)
    return urlunparse(newParsedUrl)
