### grlc

grlc, the <b>g</b>it <b>r</b>epository <b>l</b>inked data API <b>c</b>onstructor, automatically builds Web APIs using SPARQL queries stored in git repositories.

## Install and run

`git clone --recursive https://github.com/CLARIAH/grlc`
`cd grlc`
`python grlc.py`

Direct your browser to http://localhost:8088

## Usage

grlc assumes a GitHub repository (support for general git repos is on the way) where you store your SPARQL queries as .rq files. grlc will create an API operation per such a SPARQL query/.rq file.

If you're seeing this, your grlc instance is up and running, and ready to build APIs. Assuming you got it running at <code>http://localhost:8088/</code> and your queries are at <code>https://github.com/CEDAR-project/Queries</code>, just point your browser to the following locations:

- To request the swagger spec of your API, <code>http://localhost:8088/username/repo/spec</code>, e.g. <a href="http://localhost:8088/CEDAR-project/Queries/spec">http://localhost:8088/CEDAR-project/Queries/spec</a>
- To request the api-docs of your API swagger-ui style, <code>http://localhost:8088/username/repo/api-docs</code>, e.g. <a href="http://localhost:8088/CEDAR-project/Queries/api-docs">http://localhost:8088/CEDAR-project/Queries/api-docs</a>

That's it!

## Decorator syntax
A couple of SPARQL comment embedded decorators are available to make your swagger-ui look nicer (note all comments start with <code>#+ </code>):

- To create a summary of your query/operation, <code>#+ summary: This is the summary of my query/operation</code>
- To assign tags to your query/operation,
    <pre>#+ tags:
#+    - firstTag
#+    - secondTag</pre>

See examples at <a href="https://github.com/CEDAR-project/Queries">https://github.com/CEDAR-project/Queries</a>.
