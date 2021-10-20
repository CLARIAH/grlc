---
title: 'grlc: the git repository linked data API constructor.'
tags:
  - Python
  - linked data
  - API builder
authors:
  - name: Albert Meroño-Peñuela
    orcid: 0000-0003-4646-5842
    affiliation: 1
  - name: Carlos Martinez-Ortiz
    orcid: 0000-0001-5565-7577
    affiliation: 2
affiliations:
 - name: King's College London
   index: 1
 - name: Netherlands eScience Center
   index: 2
date: XX April 2020
bibliography: paper.bib
---

# Summary

RDF is a knowledge representation format (and an enabling technology for Linked Open Data) which has gained popularity over the years and it continues to be adopted in different domains such as life sciences and humanities. RDF data is typically represented as sets of triples, consisting of subject, predicate and object, and is usually stored in a triple store. SPARQL is one of the most commonly used query languages used to retrieve linked data from a triple store. However writing SPARQL queries is not a trivial task and requires some degree of expertise.

Domain experts usually face the challenge of having to learn SPARQL, when all they want is to be able to access the information contained in the triple store. Knowledge engineers with the necessary expertise can help domain experts write SPARQL queries, but they still need to modify part of the query every time they want to extract new data.

`grlc` is a lightweight server that takes SPARQL queries (stored in a GitHub repository, local file storage or listed in a URL), and translates them to Linked Data Web APIs. This enables universal access to Linked Data. Users are not required to know SPARQL to query their data, but instead can access a web API. In this way, `grlc` enables researchers to easily access knowledge represented in RDF format.

`grlc` uses the [BASIL convention](https://github.com/basilapi/basil/wiki/SPARQL-variable-name-convention-for-WEB-API-parameters-mapping) for SPARQL variable mapping and supports LD fragments [@Verborgh2016].

`grlc` has been used in a number of scientific publications [@Merono_ISWC2016,@Merono_ISWC2017,@Merono_ESWC2017,@Merono_ISWC2019] and PhD thesis [@Singh2019].

Other comparable approaches exist, which allow users to access Linked Open Data without requiring to know SPARQL; for example [OpenPHACTS](https://github.com/openphacts) and RAMOSE [@Daquino2021] are two of the most notable ones. For an extensive review of other related work, a recent survey on API approaches for knowledge graphs [@Espinoza2021].


# Acknowledgements

We acknowledge contributions from Pasquale Lisena, Richard Zijdeman and Rinke Hoekstra.

# References
