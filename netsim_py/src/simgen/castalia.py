'''
Created on Oct 14, 2014

@author: vsam
'''

import os.path
import json
from models.nsd import NSD, Network, Mote, MoteType, Position, Plan, Project
from models.json_reader import JSONReader, repository
from models.nsd import NSD, Network, Mote, MoteType, Position, \
   RFsimulation, NodeType, ConnectivityMatrix
from models.mf import Attribute
from simgen.utils import docstring_template
from .castaliagen import generate_castalia
import pdb


class NSDReader(JSONReader):
    """This class implements a text2model transformation:
    Given a datastore, it constructs an NSD model for the application.
    
    Subclassing this class, allows us to treat different "text schemas"  
    """
    def __init__(self, gen):
        self.gen = gen
        self.log = gen.log
        self.datastore = gen.datastore

    def read_nsd(self, nsd_id, simhome):
        '''
        Read an nsd and download all other linked information.
        All downloaded json objects are saved in the simulation home.

        Return the nsd object on wchich all the information is linked.
        '''
        nsd = NSD()
        self.simhome=simhome
        # get nsd

        nsd_json = self.read_object(nsd_id, nsd)
        self.create_jsonfile(nsd_json, "nsd.json")

        self.nsd=nsd
        nsd.plan = Plan()
        nsd.project = Project()

        #read Couchdb json files
        plan_json = self.read_object(nsd.plan_id, nsd.plan)
        self.create_jsonfile(plan_json, "plan.json")

        project_json = self.read_object(nsd.project_id, nsd.project)
        self.create_jsonfile(project_json, "project.json")

        # Read nodedef objects
        nodeDefOids = {n.nodeTypeId for n in nsd.plan.NodePosition}
        self.log.debug("Collected nodeDef objects: %s", nodeDefOids )

        self.nodeDefs = {oid: NodeType() for oid in nodeDefOids}
        nodeDefJson = {oid:self.read_object(oid, self.nodeDefs[oid]) 
            for oid in nodeDefOids}
        self.create_jsonfile(nodeDefJson, "nodedefs.json")
        nsd.nodedefs = set(self.nodeDefs.values())

        # read connectivity matrix, if it exists
        if ('_attachments' in plan_json and 
             'connectivityMatrix.json' in plan_json['_attachments']):
            cm = nsd.plan.connectivityMatrix = ConnectivityMatrix()
            cm_json = self.read_object((plan_json,'connectivityMatrix.json'), cm)
            self.create_jsonfile(cm_json, "connectivityMatrix.json")

        # Create network model
        self.create_network()

        return nsd

    def read_object(self, oid, obj):
        '''
        Read object oid from the repository, and populate model 
        object obj.
        '''
        entity = repository.get(obj.__class__).entity
        try:
            # read parameters
            json_obj = self.datastore.get(entity, oid)
            self.populate_modeled_instance(obj, json_obj)
        except Exception as e:
            self.log.debug("Failed to read %s." % (entity.name))
            raise RuntimeError(str(e))
        self.log.debug("%s=\n%s", entity.name, json.dumps(json_obj, indent=4))
        return json_obj

    def create_jsonfile(self, jsondata, filename):
        '''
        Creates a jsonfile with the jsondata in simhome
        '''
        with open(filename, 'w') as outfile:
            json.dump(jsondata, outfile)

    def create_network(self):
        '''

        '''
        network=Network(self.nsd)        
        for mote in self.nsd.plan.NodePosition:
            mote.network = network
            mote.nodeType = self.nodeDefs[mote.nodeTypeId]

        
        
        

#
# Implements a "driver object" mixin
#

class CastaliaGen:
    """A simulation generator targeting the Castalia simulation engine."""

    def output_file(self, path):
        """Return an open text file (for appending) with the given relative path."""
        return open(os.path.join(self.simhome, path), "a")

    def generate_nodefile(self):
        self.log.info("Generating nodefile")
        print("Generating nodefile")
        with self.open_file("nodefile.txt") as nodefile:
            nodes = self.extract_nodes(self.plan)
            nodefile.write(json.dumps(nodes))
    
    def build_model(self):
        """This is the entry point to the code that loads the NSD from the Project Repository.
        """
        self.log.info("Building model.\n simhome=%s\n sim_root=%s", self.simhome, self.sim_root)

        reader = NSDReader(self)
        self.nsd = reader.read_nsd(self.sim_root['nsdid'], self.simhome)
       
        self.log.info("NSD model built")

    
    def validate(self):

        self.log.info("NSD validated")
        
    
    def open_file(self, path):
        return open(os.path.join(self.simhome, path), "a")
        

    def generate_code(self):        
        generate_castalia(self)
        #self.generate_nodefile()


