from rdflib.plugins.sparql.parser import Query, UpdateUnit

rq = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT DISTINCT ?id ?_type (SAMPLE(?v2) as ?weaw) ?__genre_iri WHERE {
          
          ?id rdf:type ?_type.
?id rdfs:label ?v2.
OPTIONAL { ?id dbo:genre ?__genre_iri }
          
        }
LIMIT 100"""

# rq = """SELECT ?s (SAMPLE(?o) AS ?sample)
# 		WHERE {
# 			?s :dec ?o
# 		}
# """

parsed_query = Query.parseString(rq, parseAll=True)
print(parsed_query)
