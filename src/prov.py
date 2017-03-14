#!/usr/bin/env python

# prov.py: class generating grlc related W3C prov triples

from rdflib import Graph, URIRef, Namespace, RDF, Literal
import logging
from datetime import datetime
from subprocess import check_output

# grlc modules
import static as static

glogger = logging.getLogger(__name__)

class grlcPROV():
    def __init__(self, spec_uri):
        '''
        Default constructor
        '''
        self.prov_g = Graph()
        prov_uri = URIRef("http://www.w3.org/ns/prov#")
        self.prov = Namespace(prov_uri)
        self.prov_g.bind('prov', self.prov)

        self.agent = URIRef("http://{}".format(static.SERVER_NAME))
        self.entity_d = URIRef(spec_uri)
        self.activity = URIRef(self.entity_d + "-activity")

        self.init_prov_graph()

    def init_prov_graph(self):
        '''
        Initialize PROV graph with all we know at the start of the recording
        '''

        # Use git2prov to get prov on the repo
        repo_prov = check_output('git2prov', 'https://github.com/albertmeronyo/lodapi/lodapi.git', 'PROV-O')
        glogger.debug('Git2PROV output: {}'.format(repo_prov))

        self.prov_g.add( (self.agent, RDF.type, self.prov.Agent) )
        self.prov_g.add( (self.entity_d, RDF.type, self.prov.Entity) )
        self.prov_g.add( (self.activity, RDF.type, self.prov.Activity) )

        # entity_d
        self.prov_g.add( (self.entity_d, self.prov.wasGeneratedBy, self.activity) )
        self.prov_g.add( (self.entity_d, self.prov.wasAttributedTo, self.agent) )
        # later: entity_d genereated at time (when we know the end time)

        # activity
        self.prov_g.add( (self.activity, self.prov.wasAssociatedWith, self.agent) )
        self.prov_g.add( (self.activity, self.prov.startedAtTime, Literal(datetime.now())) )
        # later: activity used entity_o_1 ... entity_o_n
        # later: activity endedAtTime (when we know the end time)

    def add_used_entity(self, entity_uri):
        '''
        Add the provided URI as a used entity by the logged activity
        '''
        entity_o = URIRef(entity_uri)
        self.prov_g.add( (entity_o, RDF.type, self.prov.Entity ) )
        self.prov_g.add( (self.activity, self.prov.used, entity_o) )

    def end_prov_graph(self):
        '''
        Finalize prov recording with end time
        '''
        endTime = Literal(datetime.now())
        self.prov_g.add( (self.entity_d, self.prov.generatedAtTime, endTime) )
        self.prov_g.add( (self.activity, self.prov.endedAtTime, endTime) )

    def log_prov_graph(self):
        '''
        Log provenance graph so far
        '''
        glogger.debug("Spec generation provenance graph:")
        glogger.debug(self.prov_g.serialize(format='turtle'))

    def serialize(self, format):
        '''
        Serialize provenance graph in the specified format
        '''
        return self.prov_g.serialize(format=format)
