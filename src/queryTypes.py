# SPDX-FileCopyrightText: 2022 Albert Meroño, Rinke Hoekstra, Carlos Martínez
#
# SPDX-License-Identifier: MIT

"""Definition of grlc query types."""

qType = {
    'SPARQL': 'sparql',
    'TPF': 'tpf',
    'JSON': 'json'
}

def guessQueryType(queryUrl):
    queryUrl = queryUrl.lower()
    if queryUrl.endswith('.rq'):
        return qType['SPARQL']
    elif queryUrl.endswith('.sparql'):
        return qType['SPARQL']
    elif queryUrl.endswith('.tpf'):
        return qType['TPF']
    elif queryUrl.endswith('.json'):
        return qType['JSON']
    else:
        raise Exception('Unknown query type: ' + queryUrl)
