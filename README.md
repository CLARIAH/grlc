<p algin="center"><img src="https://raw.githubusercontent.com/CLARIAH/grlc/master/src/static/grlc_logo_01.png" width="250px"></p>

[![Join the chat at https://gitter.im/grlc](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/grlc/Lobby#)
[![DOI](https://zenodo.org/badge/46131212.svg)](https://zenodo.org/badge/latestdoi/46131212)

[![Build Status](https://travis-ci.org/c-martinez/grlc.svg?branch=cuttingEdge)](https://travis-ci.org/c-martinez/grlc)
** UPDATE build status for master branch when merged **


grlc, the <b>g</b>it <b>r</b>epository <b>l</b>inked data API <b>c</b>onstructor, automatically builds Web APIs using SPARQL queries stored in git repositories. http://grlc.io/

**Contributors:**	[Albert Meroño](https://github.com/albertmeronyo), [Rinke Hoekstra](https://github.com/RinkeHoekstra), [Carlos Martínez](https://github.com/c-martinez)

**Copyright:**	Albert Meroño, VU University Amsterdam  
**License:**	MIT License (see [LICENSE.txt](LICENSE.txt))

## What is grlc ?
grlc is a lightweight server that takes SPARQL queries curated in GitHub repositories, and translates them to Linked Data Web APIs. This enables universal access to Linked Data. Users are not required to know SPARQL to query their data, but instead can access a web API.

## Install and run

Running via [docker](https://www.docker.com/) is the easiest and preferred form of deploying grlc. You'll need a working installation of [docker](https://www.docker.com/) and [docker-compose](https://docs.docker.com/compose/). To deploy grlc, just pull the latest image from Docker hub, and run docker compose with a `docker-compose.yml` that suits your needs (an [example](docker-compose.default.yml) is provided in the root directory):

<pre>
git clone https://github.com/CLARIAH/grlc
cd grlc
docker pull clariah/grlc
docker-compose -f docker-compose.default.yml up
</pre>

(You can omit the first two commands if you just copy [this file](docker-compose.default.yml) somehwere in your filesystem)
If you use the supplied `docker-compose.default.yml` your grlc instance will be available at http://localhost:8001

In order for grlc to communicate with GitHub, you'll need to tell grlc what your access token is:

1. Get a GitHub personal access token. In your GitHub's profile page, go to _Settings_, then _Developer settings_, _Personal access tokens_, and _Generate new token_
2. You'll get an access token string, copy it and save it somewhere safe (GitHub won't let you see it again!)
3. Edit your `docker-compose.yml` or `docker-compose.default.yml` file, and paste this token as value of the environment variable GRLC_GITHUB_ACCESS_TOKEN

If you want to run grlc at system boot as a service, you can find example upstart scripts at [upstart/](upstart/grlc-docker.conf)

### Alternative install methods

Through these you'll miss some cool docker bundled features (like nginx-based caching). We provide these alternatives just for testing, development scenarios, or docker compatibility reasons.

#### pip

If you want to use grlc as a library, you'll find it useful to install via `pip`.

<pre>
pip install grlc
grlc-server
</pre>

More details can be found at [grlc's PyPi page](https://pypi.python.org/pypi/grlc/1.0) (thanks to [c-martinez](https://github.com/c-martinez)!).

#### Flask application

 you can find an example of how to run grlc natively [here](https://github.com/CLARIAH/grlc/blob/master/docker-build/entrypoint.sh#L20)

## Usage

grlc assumes a GitHub repository (support for general git repos is on the way) where you store your SPARQL queries as .rq files (like in [this one](https://github.com/CEDAR-project/Queries)). grlc will create an API operation per such a SPARQL query/.rq file.

If you're seeing this, your grlc instance is up and running, and ready to build APIs. Assuming you got it running at <code>http://localhost:8088/</code> and your queries are at <code>https://github.com/CEDAR-project/Queries</code>, just point your browser to the following locations:

- To request the swagger spec of your API, <code>http://localhost:8088/api/username/repo/spec</code>, e.g. [http://localhost:8088/api/CEDAR-project/Queries/spec](http://localhost:8088/api/CEDAR-project/Queries/spec) or [http://localhost:8088/api/CLARIAH/wp4-queries/spec](http://localhost:8088/api/CLARIAH/wp4-queries/spec)
- To request the api-docs of your API swagger-ui style, <code>http://localhost:8088/api/username/repo/api-docs</code>, e.g. [http://localhost:8088/api/CEDAR-project/Queries/api-docs](http://localhost:8088/api/CEDAR-project/Queries/api-docs) or [http://localhost:8088/api/CLARIAH/wp4-queries/api-docs](http://localhost:8088/api/CLARIAH/wp4-queries/api-docs)

By default grlc will direct your queries to the DBPedia SPARQL endpoint. To change this either:

* Add a `endpoint:` decorator in the first comment block of the query text (preferred, see below)
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
A couple of SPARQL comment embedded decorators are available to make your swagger-ui look nicer (note all comments start with <code>#+ </code>):

- To specify a query-specific endpoint, <code>#+ endpoint: http://example.com/sparql</code>.
- To indicate the HTTP request method, <code>#+ method: GET</code>.
- To paginate the results in e.g. groups of 100, <code>#+ pagination: 100</code>.
- To create a summary of your query/operation, <code>#+ summary: This is the summary of my query/operation</code>
- To assign tags to your query/operation,
    <pre>&#35;+ tags:
  &#35;+   - firstTag
  &#35;+   - secondTag</pre>
- To indicate which parameters of your query/operation should get enumerations (and get dropdown menus in the swagger-ui),
    <pre>&#35;+ enumerate:
  &#35;+   - var1
  &#35;+   - var2</pre>

  Notice that these should be plain variable names without SPARQL/BASIL conventions (so `var1` instead of `?_var1_iri`)

See examples at [https://github.com/albertmeronyo/lodapi](https://github.com/albertmeronyo/lodapi).

Use [this GitHub search](https://github.com/search?q=endpoint+summary+language%3ASPARQL&type=Code&utf8=%E2%9C%93) to see examples from other users of grlc.

## Features

- Request parameter mappings into SPARQL: grlc is compliant with [BASIL's convention](https://github.com/the-open-university/basil/wiki/SPARQL-variable-name-convention-for-WEB-API-parameters-mapping) on how to map GET/POST request parameters into SPARQL
- Automatic, user customizable population of parameter values in swagger-ui's dropdown menus via SPARQL triple pattern querying
- URL-based content negotiation: you can request for specific content types by attaching them to the operation request URL, e.g. [http://localhost:8088/CEDAR-project/Queries/residenceStatus_all.csv](http://localhost:8088/CEDAR-project/Queries/residenceStatus_all.csv) will request for results in CSV
- Pagination of API results, as per the `pagination` decorator and [GitHub's API Pagination Traversal](https://developer.github.com/guides/traversing-with-pagination/)
- Docker images in Docker Hub for easy deployment
- Compatibility with [Linked Data Fragments](http://linkeddatafragments.org/) servers, RDF dumps, and HTML+RDFa files
- Generation of provenance in [PROV](https://www.w3.org/TR/prov-primer/) of both the repo history (via [Git2PROV](https://github.com/IDLabResearch/Git2PROV)) and grlc's activity additions
- Commit-based API versioning that's coherent with the repo versioning with git hashes
- SPARQL endpoint address can be set at the query level, repository level, and now also as a query **parameter**. This makes your APIs endpoint agnostic, and enables for generic and  transposable queries!

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

## Publications

- Albert Meroño-Peñuela, Rinke Hoekstra. “grlc Makes GitHub Taste Like Linked Data APIs”. The Semantic Web – ESWC 2016 Satellite Events, Heraklion, Crete, Greece, May 29 – June 2, 2016, Revised Selected Papers. LNCS 9989, pp. 342-353 (2016). ([PDF](https://link.springer.com/content/pdf/10.1007%2F978-3-319-47602-5_48.pdf))
- Albert Meroño-Peñuela, Rinke Hoekstra. “SPARQL2Git: Transparent SPARQL and Linked Data API Curation via Git”. In: Proceedings of the 14th Extended Semantic Web Conference (ESWC 2017), Poster and Demo Track. Portoroz, Slovenia, May 28th – June 1st, 2017 (2017). ([PDF](https://www.albertmeronyo.org/wp-content/uploads/2017/04/sparql2git-transparent-sparql-4.pdf))
- Albert Meroño-Peñuela, Rinke Hoekstra. “Automatic Query-centric API for Routine Access to Linked Data”. In: The Semantic Web – ISWC 2017, 16th International Semantic Web Conference. Lecture Notes in Computer Science, vol 10587, pp. 334-339 (2017). ([PDF](https://www.albertmeronyo.org/wp-content/uploads/2017/07/ISWC2017_paper_430.pdf))
