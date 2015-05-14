'''
Created on Oct 14, 2014

@author: vsam
'''

import os.path
import json
from models.nsd import NSD, Network, Mote, MoteType, Position, Plan, Project
from models.json_reader import JSONReader
from models.nsd import NSD, Network, Mote, MoteType, Position, RFsimulation
from models.mf import Attribute
from simgen.utils import docstring_template
from .castaliagen import generate_castalia
from simgen.test_jsondata import test_read_plan, test_motedata
import pdb



def extract_jsonfile_arg(data, arg):
    for key,value in data.items():
        if key==arg:
            return value



class NSDReader(JSONReader):
    """This class implements a text2model transformation:
    Given a datastore, it constructs an NSD model for the application.
    
    Subclassing this class, allows us to treat different "text schemas"  
    """
    def __init__(self, gen):
        self.gen = gen
        self.log = gen.log
        # array storing NodeDef objects 
        self.nodeinfo=[]


    def read_nsd(self, datastore, nsd_id, simhome):
        nsd = NSD()
        self.simhome=simhome
        # get nsd
        nsd_obj = datastore.get_nsd(nsd_id)
        
        self.log.debug("NSD OBJECT=\n%s", json.dumps(nsd_obj, sort_keys=True, indent=4))
        

        try:
            # read parameters
            self.populate_modeled_instance(nsd, nsd_obj)
        except Exception as e:
            log.debug("Failed to populate NSD.", str(e))
            raise RuntimeError(str(e))

        self.nsd=nsd


        #read Couchdb json files
        self.plan= self.read_plan(datastore, self.nsd)
        self.project= self.read_project(datastore, self.nsd)
       

        #Store json objects to simhome
        self.create_jsonfile(nsd_obj, simhome, "/nsd.json")
        self.create_jsonfile(self.plan, simhome, "/plan.json")
        self.create_jsonfile(self.project, simhome, "/project.json")
        #test_read_plan(datastore, nsd)
        #Create network model
        self.create_network(datastore)

        return nsd

    #
    #Reads the  plan json file from CouchDb
    #    
    def read_plan(self, datastore, nsd):
        plan = datastore.get_plan(nsd.plan_id)
        nsd.plan = Plan()
        try:
            # read parameters
            self.populate_modeled_instance(nsd.plan, plan)
        except Exception as e:
            self.log.debug("Failed to read plan.")
            raise RuntimeError(str(e))
        return plan

    #
    #Read the  project json file from CouchDb
    #  
    def read_project(self, datastore, nsd):
        project=datastore.get_project(nsd.project_id)
        nsd.project = Project()
        self.populate_modeled_instance(nsd.project, project)
        return project

    #
    #Read the NODEDEF json object from CouhDb
    #
    def read_nodedef(self, datastore, nodedef_id):
        #assert not nodedef_id
        return datastore.get_nodedef(nodedef_id)

    #
    #Creates a jsonfile with the jsondata in simhome
    #
    def create_jsonfile(self, jsondata, simhome, filename):
        path=simhome+filename
        with open(path, 'w') as outfile:
            json.dump(jsondata, outfile)


    #
    #Extract info from couchdb json files and creates the network model
    #
    def create_network(self, datastore):

        self.network=Network(self.nsd)
        
        self.defaultMoteType=MoteType()
        
        numOfNodes= self.nsd.plan.numOfNodes
        
        for i in range(numOfNodes):
            self.create_mote(self.plan['NodePosition'][i])

        """
        #Read the NODEDEF object and store it to the nodeifo list
        nodedata=self.read_nodedef(datastore, self.plan['NodePosition'][i]['nodeTypeId'])
        nodedef=NodeDef(self.nsd, nodedata)
        self.nodeinfo.append(nodedef)

        self.read_rfsimulations(datastore, self.plan['simulations'])

        if '_attachments' in self.plan:
            self.read_attachments(datastore, self.plan['_attachments'] )
        """

    def read_rfsimulations(self, datastore, data):
        for item in data:
           # simjson=datastore.get_RFsimulation(item)
           # RFsim_def = RFsim_def(self.nsd, self.network, simjson)
            sim = RFsimulation(self.network, str(item))
            print("network", sim.network)
            print("simid", sim.simid)
        
    def read_attachments(self, datastore, attachments):
        for key,value in attachments.items():
            print("+++++++++++++++++++",key)
            cm = datastore.get_attachment(self.plan, key)
            path = self.simhome + '/' + key
            with open(path, 'wb') as outfile:
                outfile.write(bytes(int(x,0) for x in cm))
    

    def create_mote(self, data):
        mote = Mote(self.network, self.defaultMoteType)

        mote.node_id = str(data['nodeId'])
        mote.moteRole = data['nodeType']
        mote.position = Position(*[float(c) for c in data['coordinates']])
        mote.elevation = float(data['elevOfGround'])
        mote.rx_threshold = float(data['RXthreshold'])
        mote.rf_antenna_conf = data['rfAntennaConf']

        return mote      
        
        

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
        self.nsd = reader.read_nsd(self.datastore, self.sim_root['nsdid'], self.simhome)
       
        self.log.info("NSD model built")

    
    def validate(self):

        self.log.info("NSD validated")
        
    
    def open_file(self, path):
        return open(os.path.join(self.simhome, path), "a")
        

    def generate_code(self):        
        generate_castalia(self)
        #self.generate_nodefile()


   
    
#
#Class for storing NODEDEF json dicts
#
class NodeDef:

    def __init__(self, nsd_obj, jsondict):
        self.nsd=nsd_obj
        self.jsondata=jsondict

class RFsim_def:

    def __init__(self, nsd_obj, network_obj, jsondict):
        self.nsd = nsd_obj
        self.network = network_obj
        self.jsondata = jsondict



    