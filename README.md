<!--
SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez

SPDX-License-Identifier: MIT
-->

<p algin="center"><img src="https://raw.githubusercontent.com/CLARIAH/grlc/master/src/static/grlc_logo_01.png" width="250px"></p>

[![PyPI version](https://badge.fury.io/py/grlc.svg)](https://badge.fury.io/py/grlc)
[![DOI](https://zenodo.org/badge/46131212.svg)](https://zenodo.org/badge/latestdoi/46131212)
![Build Status](https://github.com/CLARIAH/grlc/actions/workflows/testing.yml/badge.svg?branch=master)
[![status](https://joss.theoj.org/papers/437074e2d77df8c6cbf3bc4e407b3b17/status.svg)](https://joss.theoj.org/papers/437074e2d77df8c6cbf3bc4e407b3b17)
[![FAIR checklist badge](https://ardc-fair-checklist.github.io/badge.svg)](https://ardc-fair-checklist.github.io/v0.2?f=31&a=32113&i=32121&r=123)


grlc, the <b>g</b>it <b>r</b>epository <b>l</b>inked data API <b>c</b>onstructor, automatically builds Web APIs using shared SPARQL queries. http://grlc.io/

If you use grlc in your work, please cite it as:

```
@InProceedings{merono2016grlc,
 author = {Mero{\~{n}}o-Pe{\~{n}}uela, Albert and Hoekstra, Rinke},
 title = {{grlc Makes GitHub Taste Like Linked Data APIs}},
 booktitle = {The Semantic Web: ESWC 2016 Satellite Events, Heraklion, Crete, Greece, May 29 -- June 2,  2016},
 year = {2016},
 publisher = {Springer},
 pages = {342--353},
 isbn = {978-3-319-47602-5},
 doi = {10.1007/978-3-319-47602-5_48}
}
```

## What is grlc?
grlc is a lightweight server that takes SPARQL queries (stored in a GitHub or GitLab repository, in your local filesystem, or listed in a URL), and translates them to Linked Data Web APIs. This enables universal access to Linked Data. Users are not required to know SPARQL to query their data, but instead can access a web API.

## Quick tutorial
For a quick usage tutorial check out our wiki [walkthrough](https://github.com/CLARIAH/grlc/wiki/Quick-tutorial) and [list of features](https://github.com/CLARIAH/grlc/wiki/Features).

## Usage
grlc assumes that you have a collection of SPARQL queries as .rq files (like [this](https://github.com/CLARIAH/grlc-queries)). grlc will create one API operation for each SPARQL query/.rq file in the collection.

Your queries can add API parameters to each operation by using the [parameter mapping](https://github.com/CLARIAH/grlc/wiki/Parameter-Mapping) syntax. This allows your query to define query variables which will be mapped to API parameters for your API operation ([see here](https://github.com/CLARIAH/grlc-queries/blob/master/enumerate.rq) for an example).

Your queries can include special [decorators](#decorator-syntax) to add extra functionality to your API.

grlc also supports SPARQL queries expressed as json, using the [SPARQL Transformer](https://github.com/D2KLab/py-sparql-transformer) [Query in JSON](https://github.com/D2KLab/sparql-transformer/blob/master/README.md#query-in-json) syntax. (**Tip**: the [SPARQL Transformer Playground](https://d2klab.github.io/sparql-transformer/) is very useful when building queries with this syntax).

### Query location
grlc can load your query collection from different locations: from a GitHub repository (`api-git`), from a GitLab repository (`api-gitlab`), from local storage (`api-local`), and from a specification file (`api-url`). Each type of location has specific features and is accessible via different paths. However all location types produce the same beautiful APIs.

#### From a GitHub repository
> API path:
`http://grlc-server/api-git/<user>/<repo>`

grlc can build an API from any Github repository, specified by the GitHub user name of the owner (`<user>`) and repository name (`<repo>`).

For example, assuming your queries are stored on a Github repo: `https://github.com/CLARIAH/grlc-queries/`, point your browser to the following location
`http://grlc.io/api-git/CLARIAH/grlc-queries/`

grlc can make use of git's version control mechanism to generate an API based on a specific version of queries in the repository. This can be done by including the commit sha in the URL path (`http://grlc-server/api-git/<user>/<repo>/commit/<sha>`), for example: `http://grlc.io/api-git/CLARIAH/grlc-queries/commit/79ceef2ee814a12e2ec572ffaa2f8212a22bae23`

grlc can also use a subdirectory inside your Github repo. This can be done by including a subdirectory in the URL path (`http://grlc-server/api-git/<user>/<repo>/subdir/<subdir>`).

#### From a GitLab repository
> API path:
`http://grlc-server/api-gitlab/<user>/<repo>`

grlc can build an API from any GitLab repository, specified by the GitLab user name of the owner (`<user>`) and repository name (`<repo>`).

For example, assuming your queries are stored on a GitLab repo: `https://gitlab.com/c-martinez/grlc-queries`, point your browser to the following location
`http://grlc.io/api-gitlab/c-martinez/grlc-queries/`

grlc can make use of git's version control mechanism to generate an API based on a specific version of queries in the repository. This can be done by including the name of a branch in the URL path (`http://grlc-server/api-gitlab/<user>/<repo>/branch/<branch>`), for example: `http://grlc.io/api-gitlab/c-martinez/grlc-queries/branch/master`

grlc can also use a subdirectory inside your GitLab repo. This can be done by including a subdirectory in the URL path (`http://grlc-server/api-gitlab/<user>/<repo>/subdir/<subdir>`), for example: `http://grlc-server/api-gitlab/c-martinez/grlc-queries/subdir/subdir`.

#### From local storage
> API path:
`http://grlc-server/api-local/`

grlc can generate an API from a local directory in the computer where your grlc server runs. You can configure the location of this directory in your [grlc server configuration file](#grlc-server-configuration). See also [how to install and run your own grlc instance](#install-and-run).

When the API is generated from a local directory, API information can be loaded from a configuration file in that folder. This file must be called `local-api-config.ini` and it has the following format:
```ini
[repo_info]
repo_title = Some title
api_description = Description of my API
contact_name = My name
contact_url = https://mypage/
licence_url = https://mylicence/
```

#### From a specification file
> API path:
`http://grlc-server/api-url/?specUrl=<specUrl>`

grlc can generate an API from a yaml specification file accessible on the web.

For example, assuming your queries are listed on spec file: `https://raw.githubusercontent.com/CLARIAH/grlc-queries/master/urls.yml`, point your browser to the following location
`http://grlc.io/api-url?specUrl=https://raw.githubusercontent.com/CLARIAH/grlc-queries/master/urls.yml`

##### Specification file syntax
A grlc API specification file is a YAML file which includes the necessary information to create a grlc API, most importantly a list of URLs to decorated and HTTP-dereferenceable SPARQL queries. This file should contain the following fields

 - `title`: Title of my API
 - `description`: API description
 - `contact`: Contact details of the API owner. This should include the `name` and `url` properties.
 - `licence`: A URL pointing to the licence file for the API.
 - `queries`: A list of URLs of SPARQL queries (with header decorators). Alternatively a query can be defined as a dictionary with a `name` and a `url`.

For example:
```YAML
title: Title of my API
description: Description of my API
contact:
  name: Contact Name
  url: https://www.mywebsite.org
licence: http://example.org/licence.html
queries:
  - https://www.mywebsite.org/query1.rq
  - https://www.mywebsite.org/query2.rq
  - https://www.otherwebsite.org/query3.rq
  - name: QueryFour
    url: https://www.mywebsite.org/query4.rq
```

### grlc generated API

The API paths of all location types point to the generated [swagger-ui](https://swagger.io/) style API documentation. On the API documentation page, you can explore available API calls and execute individual API calls.

You can also view the swagger spec of your API, by visiting `<API-path>/swagger`, for example: `http://grlc.io/api-git/CLARIAH/grlc-queries/swagger`

### grlc query execution
When you call an API endpoint, grlc executes the SPARQL query for that endpoint by combining supplied parameters and decorators.

There are 4 options to specify your own endpoint:

* Add a `sparql_endpoint` on your [`config.ini`](#grlc-server-configuration)
* Add a `endpoint` parameter to your request: 'http://grlc.io/user/repo/query?endpoint=http://sparql-endpoint/'. You can add a `#+ endpoint_in_url: False` decorator if you DO NOT want to see the `endpoint` parameter in the swagger-ui of your API.
* Add the `#+ endpoint:` [decorator](#`endpoint`).
* Add the URL of the endpoint on a single line in an `endpoint.txt` file within the GitHub repository that contains the queries.

The endpoint call will return the result of executing the query as a json representation of rdflib.query.QueryResult (for other result formats, you can use content negotiation via HTTP `Accept` headers). For json responses, the schema of the response can be modified by using the `#+ transform:` [decorator](#`transform`).

## Decorator syntax
Special decorators are available to make your swagger-ui look nicer and to increase functionality. These are provided as comments at the start of your query file, making it still syntactically valid SPARQL. All decorators start with `#+ `, for example:

```SPARQL
#+ decorator_1: decorator value
#+ decorator_1: decorator value

SELECT * WHERE {
  ?s ?p ?o .
}
```
The following is a list of available decorators and their function:

### `summary`
Creates a summary of your query/operation. This is shown next to your operation name in the swagger-ui.

Syntax:
```
#+ summary: This is the summary of my query/operation
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/summary.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_summary).

### `description`
Creates a description of your query/operation. This is shown as the description of your operation in the swagger-ui.

Syntax:
```
#+ description: Extended description of my query/operation.
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/description.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_description).

### `endpoint`
Specifies a query-specific endpoint.

Syntax:
```
#+ endpoint: http://example.com/sparql
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/endpoint.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_endpoint).

### `pagination`
Paginates the results in groups of (for example) 100. Links to previous, next, first, and last result pages are provided as HTTP response headers to avoid polluting the payload (see details [here](https://developer.github.com/v3/guides/traversing-with-pagination/))

Syntax:
```
#+ pagination: 100
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/pagination.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_pagination).

### `method`
Indicates the HTTP request method (`GET` and `POST` are supported).

Syntax:
```
#+ method: GET
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/method.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/post_method).

### `tags`
Assign tags to your query/operation. Query/operations with the same tag are grouped together in the swagger-ui.

Syntax:
```
#+ tags:
#+   - firstTag
#+   - secondTag
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/tags.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/group1/get_tags).

### `defaults`
Set the default value in the swagger-ui for a specific parameter in the query.

Syntax:
```
#+ defaults:
#+   - param_name: default_value
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/defaults.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_defaults).

### `enumerate`
Indicates which parameters of your query/operation should get enumerations (and get dropdown menus in the swagger-ui) using the given values from the SPARQL endpoint. The values for each enumeration variable can also be specified into the query decorators to save endpoint requests and speed up the API generation.

Syntax:
```
#+ enumerate:
#+   - var1:
#+     - value1
#+     - value2
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/enumerate.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_enumerate).

Notice that these should be plain variable names without SPARQL/BASIL conventions (so `var1` instead of `?_var1_iri`)

###  `endpoint_in_url`
Allows/disallows the `endpoint` parameter from being provided as a URL parameter (allowed by default).

Syntax:
```
#+ endpoint_in_url: False
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/endpoint_url.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_endpoint_url).

###  `transform`
Allows  query results to be converted to the specified JSON structure, by using [SPARQLTransformer](https://github.com/D2KLab/py-sparql-transformer) syntax. Notice that the response content type must be set to `application/json` for the transformation to take effect.

Syntax:
```
#+ transform: {
#+     "key": "?p",
#+     "value": "?o",
#+     "$anchor": "key"
#+   }
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/transform.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_transform).

### `endpoint-method`
Allows the query to be sent from the grlc server to the SPARQL endpoint using either `GET` or `POST` http method. (Default: `POST`)

Syntax:
```
#+ endpoint-method: GET
```

Example [query](https://github.com/CLARIAH/grlc-queries/blob/master/endpoint-method.rq) and the equivalent [API operation](http://grlc.io/api-git/CLARIAH/grlc-queries/#/default/get_endpoint_method).

### Example APIs

Check these out:
- http://grlc.io/api-git/CLARIAH/grlc-queries
- http://grlc.io/api-gitlab/c-martinez/grlc-queries
- http://grlc.io/api-url?specUrl=https://raw.githubusercontent.com/CLARIAH/grlc-queries/master/urls.yml
- http://grlc.io/api-git/CLARIAH/wp4-queries-hisco
- http://grlc.io/api-git/albertmeronyo/lodapi
- http://grlc.io/api-git/albertmeronyo/lsq-api
- https://grlc.io/api-git/CEDAR-project/Queries

You'll find the sources of these and many more in [GitHub](https://github.com/search?o=desc&q=endpoint+summary+language%3ASPARQL&s=indexed&type=Code&utf8=%E2%9C%93)

Use [this GitHub search](https://github.com/search?q=endpoint+summary+language%3ASPARQL&type=Code&utf8=%E2%9C%93) to see examples from other grlc users.

## Install and run
You can use grlc in different ways:
 - [Via grlc.io](#grlc.io): you can use the [grlc.io service](https://grlc.io/)
 - [Via Docker](#Docker): you can use the [grlc docker image](https://hub.docker.com/r/clariah/grlc) and start your own grlc server.
 - [Via pip](#Pip): you can install the [grlc Python package](https://pypi.org/project/grlc/) and start your own grlc server or use grlc as a Python library.

More details for each of these options are given below.

### grlc.io
The easiest way to use grlc is by visiting [grlc.io](http://grlc.io/) and using this service to convert SPARQL queries into a RESTful API. Your queries can be [stored on a github repo](#from-a-github-repository) or can be [listed on a specification file](#from-a-specification-file).

#### Google Analytics
grlc.io uses Google Analytics to keep track of the number of users of the service. We need this to show the impact of grlc when applying for funding. If this causes you to be conserned about privacy, we recommend you use some user-side anti-tracking, and we would appreciate if you could reach out to us to let us know you are using grlc.

### Docker
To run grlc via [docker](https://www.docker.com/), you'll need a working installation of docker. To deploy grlc, just pull the [latest image from Docker hub](https://hub.docker.com/r/clariah/grlc/). :
```bash
docker run -it --rm -p 8088:80 clariah/grlc
```

The docker image allows you to setup several environment variable such as `GRLC_SERVER_NAME` `GRLC_GITHUB_ACCESS_TOKEN`,`GRLC_GITLAB_ACCESS_TOKEN` and `GRLC_SPARQL_ENDPOINT`:
```bash
docker run -it --rm -p 8088:80 -e GRLC_SERVER_NAME=grlc.io -e GRLC_GITHUB_ACCESS_TOKEN=xxx -e GRLC_GITLAB_ACCESS_TOKEN=yyy -e GRLC_SPARQL_ENDPOINT=http://dbpedia.org/sparql -e DEBUG=true clariah/grlc
```

### Pip
If you want to run grlc locally or use it as a library, you can install grlc on your machine. Grlc is [registered in PyPi](https://pypi.org/project/grlc/) so you can install it using pip.

#### Prerequisites
grlc has the following requirements:
- Python3
- development files (depending on your OS):
```bash
sudo apt-get install libevent-dev python-all-dev
```

#### pip install
Once the base requirements are satisfied, you can install grlc like this:
```bash
pip install grlc
```

Once grlc is installed, you have several options:
 - [Stand alone server](#Standalone-server)
 - [Using a WSGI server](#Using-a-WSGI-server)
 - [As a python library](#Grlc-library)

#### Standalone server
grlc includes a command line tool which you can use to start your own grlc server:
```bash
grlc-server
```

#### Using a WSGI server
You can run grlc using a WSGI server such as gunicorn as follows:
```bash
gunicorn grlc.server:app
```

If you want to use your own gunicorn configuration, for example `gunicorn_config.py`:
```python
workers = 5
worker_class = 'gevent'
bind = '0.0.0.0:8088'
```
Then you can run it as:
```bash
gunicorn -c gunicorn_config.py grlc.server:app
```

**Note:** Since `gunicorn` does not work under Windows, you can use `waitress` instead:
```bash
waitress-serve --port=8088 grlc.server:app
```

If you want to run grlc at system boot as a service, you can find example upstart scripts at [upstart/](upstart/grlc-docker.conf)

#### grlc library
You can use grlc as a library directly from your own python script. See the [usage example](https://github.com/CLARIAH/grlc/blob/master/doc/notebooks/GrlcFromNotebook.ipynb) to find out more.

#### grlc server configuration
Regardless of how you are running your grlc server, you will need to configure it using the `config.ini` file. Have a look at the [example config file](./config.default.ini) to see how it this file is structured.

The configuration file contains the following variables:
 - `github_access_token` [access token](#gitaccess-token) to communicate with Github API.
 - `gitlab_access_token` [access token](#git-access-token) to communicate with GitLab API.
 - `local_sparql_dir` local storage directory where [local queries](#from-local-storage) are located.
 - `server_name` name of the server (e.g. grlc.io)
 - `sparql_endpoint` default SPARQL endpoint
 - `user` and `password` SPARQL endpoint default authentication (if required, specify `'none'` if not required)
 - `debug` enable debug level logging.
 - `gitlab_url` to specify the base url of your GitLab instance.

##### Git access token
In order for grlc to communicate with GitHub and/or GitLab, you'll need to tell grlc what your access token is:

1. Get a [GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#authenticating-to-the-api-with-a-personal-access-token) or [GitLab personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token).
2. You'll get an access token string, copy it and save it somewhere safe.
3. Edit your `config.ini` (`github_access_token` and `gitlab_access_token` respectively) and/or `docker-compose.yml` (`GRLC_GITHUB_ACCESS_TOKEN` and `GRLC_GITLAB_ACCESS_TOKEN` environment variables).

# Contribute!
grlc needs **you** to continue bringing Semantic Web content to developers, applications and users. No matter if you are just a curious user, a developer, or a researcher; there are many ways in which you can contribute:

- File in bug reports
- Request new features
- Set up your own environment and start hacking

Check our [contributing](CONTRIBUTING.md) guidelines for these and more, and join us today!

If you cannot code, that's no problem! There's still plenty you can contribute:

- Share your experience at using grlc in Twitter (mention the handle **@grlcldapi**)
- If you are good with HTML/CSS, [let us know](mailto:albert.meronyo@gmail.com)

## Related tools
- [SPARQL2Git](https://github.com/albertmeronyo/SPARQL2Git) is a Web interface for editing SPARQL queries and saving them in GitHub as grlc APIs.
- [grlcR](https://github.com/CLARIAH/grlcR) is a package for R that brings Linked Data into your R environment easily through grlc.
- [Hay's tools](https://tools.wmflabs.org/hay/directory/#/showall) lists grlc as a Wikimedia-related tool :-)

## This is what grlc users are saying
- [Flavour your Linked Data with grlc](https://blog.esciencecenter.nl/flavour-your-linked-data-with-garlic-98bfbb358e06), by Carlos Martinez
- [Converting any SPARQL endpoint to an OpenAPI](http://chem-bla-ics.blogspot.com/2018/07/converting-any-sparql-endpoint-to.html) by Egon Willighagen

Quotes from grlc users:
> A cool project that can convert a random SPARQL endpoint into an OpenAPI endpoint

> It enables us to quickly integrate any new API requirements in a matter of seconds, without having to worry about configuration or deployment of the system

> You can store your SPARQL queries on GitHub and then you can run your queries on your favourite programming language (Python, Javascript, etc.) using a Web API (including swagger documentation) just as easily as loading data from a web page

**Contributors:**	[Albert Meroño](https://github.com/albertmeronyo), [Rinke Hoekstra](https://github.com/RinkeHoekstra), [Carlos Martínez](https://github.com/c-martinez)

**Copyright:**	Albert Meroño, Rinke Hoekstra, Carlos Martínez  
**License:**	MIT License (see [LICENSE.txt](LICENSE.txt))

## Academic publications

- Albert Meroño-Peñuela, Carlos Martinez-Ortiz. “grlc: the git repository linked data API constructor.“ Journal of Open Source Software, 6(67), 2731 (2021), <https://doi.org/10.21105/joss.02731>
- Albert Meroño-Peñuela, Pasquale Lisena, Carlos Martínez-Ortiz. “Web Data APIs for Knowledge Graphs: Easing Access to Semantic Data for Application Developers”. Synthesis Lectures on Data, Semantics, and Knowledge, 12(1), pp.1-118 (2021) (Morgan & Claypool) <https://doi.org/10.2200/S01114ED1V01Y202107DSK021>
- Albert Meroño-Peñuela, Rinke Hoekstra. “grlc Makes GitHub Taste Like Linked Data APIs”. The Semantic Web – ESWC 2016 Satellite Events, Heraklion, Crete, Greece, May 29 – June 2, 2016, Revised Selected Papers. LNCS 9989, pp. 342-353 (2016). ([PDF](https://link.springer.com/content/pdf/10.1007%2F978-3-319-47602-5_48.pdf))
- Albert Meroño-Peñuela, Rinke Hoekstra. “SPARQL2Git: Transparent SPARQL and Linked Data API Curation via Git”. In: Proceedings of the 14th Extended Semantic Web Conference (ESWC 2017), Poster and Demo Track. Portoroz, Slovenia, May 28th – June 1st, 2017 (2017). ([PDF](https://www.albertmeronyo.org/wp-content/uploads/2017/04/sparql2git-transparent-sparql-4.pdf))
- Albert Meroño-Peñuela, Rinke Hoekstra. “Automatic Query-centric API for Routine Access to Linked Data”. In: The Semantic Web – ISWC 2017, 16th International Semantic Web Conference. Lecture Notes in Computer Science, vol 10587, pp. 334-339 (2017). ([PDF](https://www.albertmeronyo.org/wp-content/uploads/2017/07/ISWC2017_paper_430.pdf))
- Pasquale Lisena, Albert Meroño-Peñuela, Tobias Kuhn, Raphaël Troncy. “Easy Web API Development with SPARQL Transformer”. In: The Semantic Web – ISWC 2019, 18th International Semantic Web Conference. Lecture Notes in Computer Science, vol 11779, pp. 454-470 (2019). ([PDF](https://www.albertmeronyo.org/wp-content/uploads/2019/06/ISWC2019_paper_237.pdf))
