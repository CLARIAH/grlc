<p algin="center"><img src="https://raw.githubusercontent.com/CLARIAH/grlc/master/src/static/grlc_logo_01.png" width="250px"></p>

[![Join the chat at https://gitter.im/grlc](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/grlc/Lobby#)
[![DOI](https://zenodo.org/badge/46131212.svg)](https://zenodo.org/badge/latestdoi/46131212)
[![Build Status](https://travis-ci.org/CLARIAH/grlc.svg?branch=master)](https://travis-ci.org/CLARIAH/grlc)


grlc, the <b>g</b>it <b>r</b>epository <b>l</b>inked data API <b>c</b>onstructor, automatically builds Web APIs using SPARQL queries stored in git repositories. http://grlc.io/

> A cool project that can convert a random SPARQL endpoint into an OpenAPI endpoint

> It enables us to quickly integrate any new API requirements in a matter of seconds, without having to worry about configuration or deployment of the system

> You can store your SPARQL queries on GitHub and then you can run your queries on your favourite programming language (Python, Javascript, etc.) using a Web API (including swagger documentation) just as easily as loading data from a web page

**Contributors:**	[Albert Meroño](https://github.com/albertmeronyo), [Rinke Hoekstra](https://github.com/RinkeHoekstra), [Carlos Martínez](https://github.com/c-martinez)

**Copyright:**	Albert Meroño, VU University Amsterdam  
**License:**	MIT License (see [LICENSE.txt](LICENSE.txt))

## What is grlc ?
grlc is a lightweight server that takes SPARQL queries curated in GitHub repositories, and translates them to Linked Data Web APIs. This enables universal access to Linked Data. Users are not required to know SPARQL to query their data, but instead can access a web API.

## Quick tutorial
For a quick usage tutorial check out our wiki walkthrough [here](https://github.com/CLARIAH/grlc/wiki/Quick-tutorial)

## Features

- Request parameter mappings into SPARQL: grlc is compliant with [BASIL's convention](https://github.com/the-open-university/basil/wiki/SPARQL-variable-name-convention-for-WEB-API-parameters-mapping) on how to map GET/POST request parameters into SPARQL
- Automatic, user customizable population of parameter values in swagger-ui's dropdown menus via SPARQL triple pattern querying
- Parameter values as enumerations (i.e. closed lists of values that will fill a dropdown in the UI) can now also be specified in the query decorators to save endpoint requests (see [this example](https://github.com/albertmeronyo/lodapi/blob/master/houseType_params.rq))
- Parameter default values can now also be indicated through decorators (see [this example](https://github.com/albertmeronyo/lodapi/blob/master/dbpedia_test.rq))
- URL-based content negotiation: you can request for specific content types by attaching them to the operation request URL, e.g. [http://localhost:8088/CEDAR-project/Queries/residenceStatus_all.csv](http://localhost:8088/CEDAR-project/Queries/residenceStatus_all.csv) will request for results in CSV
- Pagination of API results, as per the `pagination` decorator and [GitHub's API Pagination Traversal](https://developer.github.com/guides/traversing-with-pagination/)
- Docker images in Docker Hub for easy deployment
- Compatibility with [Linked Data Fragments](http://linkeddatafragments.org/) servers, RDF dumps, and HTML+RDFa files
- **[NEW]** grlc integrates now [SPARQLTransformer](https://github.com/D2KLab/py-sparql-transformer), allowing the use of queries in JSON (see [this example](https://github.com/albertmeronyo/lodapi/blob/master/dbpedia_test_json.json)).
- Generation of provenance in [PROV](https://www.w3.org/TR/prov-primer/) of both the repo history (via [Git2PROV](https://github.com/IDLabResearch/Git2PROV)) and grlc's activity additions
- Commit-based API versioning that's coherent with the repo versioning with git hashes
- SPARQL endpoint address can be set at the query level, repository level, and now also as a query **parameter**. This makes your APIs endpoint agnostic, and enables for generic and transposable queries!
- CONSTRUCT queries are now mapped automatically to GET requests, accept parameters in the WHERE clause, and return content in ``text/turtle`` or ``application/ld+json``
- INSERT DATA queries are now mapped automatically to POST requests. Support is limited to queries with no WHERE clause, and parameters are always expected to be values for ``g`` (named graph where to insert the data) and ``data`` (with the triples to insert, in ``ntriples`` format). The INSERT query pattern is so far static, as defined in [static.py](https://github.com/CLARIAH/grlc/blob/master/src/static.py#L61). Only tested with Virtuoso.

## Install and run

### grlc.io
The easiest way to use grlc is by visiting [grlc.io/](http://grlc.io/) and using this service to convert SPARQL queries on your github repo into a RESTful API.

### Pip
If you want to run grlc locally or use it as a library, you can install grlc on your machine. Grlc is [registered in PyPi](https://pypi.org/project/grlc/) so you can install it using pip.

#### Prerequisites
- Python3
- development files:
```bash
sudo apt-get install libevent-dev python-all-dev
```

#### pip install
```bash
pip install grlc
```

Grlc includes a command line tool which you can use to start your own grlc server:
```bash
grlc-server
```

#### Using gunicorn
You can run grlc using gunicorn as follows:
```bash
gunicorn grlc.server:app
```

If you want to use your own gunicorn configuration, for example `gunicorn_config.py`:
```
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

#### Grlc library
You can use grlc as a library directly from your own python script. See the [usage example](https://github.com/CLARIAH/grlc/blob/master/doc/notebooks/GrlcFromNotebook.ipynb) to find out more.

### Docker
To run grlc via [docker](https://www.docker.com/), you'll need a working installation of docker. To deploy grlc, just pull the [latest image from Docker hub](https://hub.docker.com/r/clariah/grlc/). :
```bash
docker run -it --rm -p 8088:80 clariah/grlc
```

The docker image allows you to setup several environment variable such as `GRLC_SERVER_NAME` `GRLC_GITHUB_ACCESS_TOKEN` and `GRLC_SPARQL_ENDPOINT`:
```bash
docker run -it --rm -p 8088:80 -e GRLC_SERVER_NAME=grlc.io -e GRLC_GITHUB_ACCESS_TOKEN=xxx -e GRLC_SPARQL_ENDPOINT=http://dbpedia.org/sparql -e DEBUG=true clariah/grlc
```

## Access token

In order for grlc to communicate with GitHub, you'll need to tell grlc what your access token is:

1. Get a GitHub personal access token. In your GitHub's profile page, go to _Settings_, then _Developer settings_, _Personal access tokens_, and _Generate new token_
2. You'll get an access token string, copy it and save it somewhere safe (GitHub won't let you see it again!)
3. Edit your `docker-compose.yml` or `docker-compose.default.yml` file, and paste this token as value of the environment variable GRLC_GITHUB_ACCESS_TOKEN

If you want to run grlc at system boot as a service, you can find example upstart scripts at [upstart/](upstart/grlc-docker.conf)

## Usage

grlc assumes a GitHub repository (support for general git repos is on the way) where you store your SPARQL queries as .rq files (like in [this one](https://github.com/CEDAR-project/Queries)). grlc will create an API operation per such a SPARQL query/.rq file.

If you're seeing this, your grlc instance is up and running, and ready to build APIs. Assuming you got it running at <code>http://localhost:8088/</code> and your queries are at <code>https://github.com/CEDAR-project/Queries</code>, just point your browser to the following locations:

- To request the swagger spec of your API, <code>http://localhost:8088/api/username/repo/spec</code>, e.g. [http://localhost:8088/api/CEDAR-project/Queries/spec](http://localhost:8088/api/CEDAR-project/Queries/spec) or [http://localhost:8088/api/CLARIAH/wp4-queries/spec](http://localhost:8088/api/CLARIAH/wp4-queries/spec)
- To request the api-docs of your API swagger-ui style, <code>http://localhost:8088/api/username/repo/api-docs</code>, e.g. [http://localhost:8088/api/CEDAR-project/Queries/api-docs](http://localhost:8088/api/CEDAR-project/Queries/api-docs) or [http://localhost:8088/api/CLARIAH/wp4-queries/api-docs](http://localhost:8088/api/CLARIAH/wp4-queries/api-docs)

By default grlc will direct your queries to the DBPedia SPARQL endpoint. To change this either:
* Add a `endpoint` parameter to your request: 'http://grlc.io/user/repo/query?endpoint=http://sparql-endpoint/'. You can add a `#+ endpoint_in_url: False` decorator if you DO NOT want to see the `endpoint` parameter in the swagger-ui of your API.
* Add a `#+ endpoint:` decorator in the first comment block of the query text (preferred, see below)
* Add the URL of the endpoint on a single line in an `endpoint.txt` file within the GitHub repository that contains the queries.
* Or you can directly modify the grlc source code (but it's nicer if the queries are self-contained)

That's it!

### Example APIs

Check these out:

- http://grlc.io/api/CLARIAH/wp4-queries-hisco/
- http://grlc.io/api/albertmeronyo/lodapi/
- http://grlc.io/api/albertmeronyo/lsq-api

You'll find the sources of these and many more in [GitHub](https://github.com/search?o=desc&q=endpoint+summary+language%3ASPARQL&s=indexed&type=Code&utf8=%E2%9C%93)

## Decorator syntax
A couple of SPARQL comment embedded decorators are available to make your swagger-ui look nicer (note all comments start with <code>#+ </code> and the use of `':'` is restricted to list-representations and cannot be used in the summary text):

- To specify a query-specific endpoint, <code>#+ endpoint: http://example.com/sparql</code>.
- To indicate the HTTP request method, <code>#+ method: GET</code>.
- To paginate the results in e.g. groups of 100, <code>#+ pagination: 100</code>.
- To create a summary of your query/operation, <code>#+ summary: This is the summary of my query/operation</code>
- To assign tags to your query/operation,
    <pre>&#35;+ tags:
  &#35;+   - firstTag
  &#35;+   - secondTag</pre>
- To indicate which parameters of your query/operation should get enumerations (and get dropdown menus in the swagger-ui) using values from the SPARQL endpoint,
    <pre>&#35;+ enumerate:
  &#35;+   - var1
  &#35;+   - var2</pre>
- These parameters can also be hard-coded into the query decorators to save endpoint requests and speed up the API generation:
<pre>&#35;+ enumerate:
&#35;+   - var1:
&#35;+     - value1
&#35;+     - value2</pre>

  Notice that these should be plain variable names without SPARQL/BASIL conventions (so `var1` instead of `?_var1_iri`)

See examples at [https://github.com/albertmeronyo/lodapi](https://github.com/albertmeronyo/lodapi).

Use [this GitHub search](https://github.com/search?q=endpoint+summary+language%3ASPARQL&type=Code&utf8=%E2%9C%93) to see examples from other users of grlc.

## Contribute!

grlc needs **you** to continue bringing Semantic Web content to developers, applications and users. No matter if you are just a curious user, a developer, or a researcher; there are many ways in which you can contribute:

- File in bug reports
- Request new features
- Set up your own environment and start hacking

Check our [contributing](CONTRIBUTING.md) guidelines for these and more, and join us today!

If you cannot code, that's no problem! There's still plenty you can contribute:

- Share your experience at using grlc in Twitter (mention the handler **@grlcldapi**)
- If you are good with HTML/CSS, [let us know](mailto:albert.merono@vu.nl)

## Related tools

- [SPARQL2Git](https://github.com/albertmeronyo/SPARQL2Git) is a Web interface for editing SPARQL queries and saving them in GitHub as grlc APIs.
- [grlcR](https://github.com/CLARIAH/grlcR) is a package for R that brings Linked Data into your R environment easily through grlc.
- [Hay's tools](https://tools.wmflabs.org/hay/directory/#/showall) lists grlc as a Wikimedia-related tool :-)

## This is what grlc users are saying

- [Flavour your Linked Data with grlc](https://blog.esciencecenter.nl/flavour-your-linked-data-with-garlic-98bfbb358e06), by Carlos Martinez
- [Egon Willighagen's blog](http://chem-bla-ics.blogspot.com/2018/07/converting-any-sparql-endpoint-to.html)

## Academic publications

- Albert Meroño-Peñuela, Rinke Hoekstra. “grlc Makes GitHub Taste Like Linked Data APIs”. The Semantic Web – ESWC 2016 Satellite Events, Heraklion, Crete, Greece, May 29 – June 2, 2016, Revised Selected Papers. LNCS 9989, pp. 342-353 (2016). ([PDF](https://link.springer.com/content/pdf/10.1007%2F978-3-319-47602-5_48.pdf))
- Albert Meroño-Peñuela, Rinke Hoekstra. “SPARQL2Git: Transparent SPARQL and Linked Data API Curation via Git”. In: Proceedings of the 14th Extended Semantic Web Conference (ESWC 2017), Poster and Demo Track. Portoroz, Slovenia, May 28th – June 1st, 2017 (2017). ([PDF](https://www.albertmeronyo.org/wp-content/uploads/2017/04/sparql2git-transparent-sparql-4.pdf))
- Albert Meroño-Peñuela, Rinke Hoekstra. “Automatic Query-centric API for Routine Access to Linked Data”. In: The Semantic Web – ISWC 2017, 16th International Semantic Web Conference. Lecture Notes in Computer Science, vol 10587, pp. 334-339 (2017). ([PDF](https://www.albertmeronyo.org/wp-content/uploads/2017/07/ISWC2017_paper_430.pdf))
