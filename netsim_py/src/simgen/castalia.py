'''
Created on Oct 14, 2014

@author: vsam
'''

import os.path
import json
from models.nsd import NSD, Network, Mote, MoteType
from models.mf import Attribute
from simgen.utils import docstring_template
from .castaliagen import generate_castalia
import pdb


def transform_value(attr, value):
    """Transform a value so that it is assignment-compatible the given mf.Attribute.
    """
    assert isinstance(attr, Attribute)
    
    if isinstance(value, attr.type):
        return value 
    if attr.nullable and value is None:
        return value
    
    try:
        # try a default python conversion
        tval = attr.type(value)
        return tval
    except:
        # We have failed, return the untranslated value so that there is an error at a higher layer
        return value


def populate_modeled_instance(model, json):
    """Given a model object and a json dict, fill in the attributes of model
    from the json dict.
    
    This method will cast certain types to others, using transform_value.
    """
    
    metamodel = model.__model_class__
    
    for attr in metamodel.attributes:
        json_field = attr.name  # here we can add a mapping!
      #  pdb.set_trace()
        if json_field in json:
        
            tval = transform_value(attr, json[json_field])
            setattr(model, attr.name, tval)


def extract_jsonfile_arg(data, arg):
    for key,value in data.items():
        if key==arg:
            return value



class NSDReader:
    """This class implements a text2model transformation:
    Given a datastore, it constructs an NSD model for the application.
    
    Subclassing this class, allows us to treat different "text schemas"  
    """
    
    def read_nsd(self, datastore, nsd_id, simhome):
        nsd = NSD()
        
        # get nsd
        nsd_obj = datastore.get_nsd(nsd_id)
        
        # read parameters
        populate_modeled_instance(nsd, nsd_obj)
        self.nsd=nsd
        self.plan= self.read_plan(datastore, self.nsd)
        self.project= self.read_project(datastore, self.nsd)
        self.create_network()

        return nsd

    #
    #Reads the corresponding plan json file from CouchDb
    #    
    def read_plan(self, datastore, nsd):
        planid=nsd.plan_id
        plan=datastore.get_plan(planid)
        populate_modeled_instance(nsd, plan)
        return plan

    #
    #Reads the corresponding project json file from CouchDb
    #  
    def read_project(self, datastore, nsd):
        projectid=nsd.project_id
        project=datastore.get_project(projectid)
        populate_modeled_instance(nsd, project)
        return project

    #
    #Extract info from couchdb json files and creates the network model
    #
    def create_network(self):
        self.network=Network(self.nsd)
        self.defaultMoteType=MoteType()
        numOfNodes=int(self.nsd.numOfNodes)
        for i in range (0, numOfNodes):
            self.create_mote(self.plan['NodePosition'][i])

    def create_mote(self, data):
        mote=Mote(self.network, self.defaultMoteType)
        setattr(mote, 'node_id', transform_value(str, data["nodeId"]))
        setattr(mote, Position, transform_value('Position', data['coordinates'][0], data['coordinates'][1], data['coordinates'][2]))
   
        
        

#
# Implements a "driver object" mixin
#

class CastaliaGen:
    """A simulation generator targeting the Castalia simulation engine."""

    def output_file(self, path):
        """Return an open text file (for appending) with the given relative path."""
        return open(os.path.join(self.simhome, path), "a")

    def generate_nodefile(self):
        self.log.info("Generating `nodefile")
        print("Generating nodefile")
        with self.open_file("nodefile.txt") as nodefile:
            nodes = self.extract_nodes(self.plan)
            nodefile.write(json.dumps(nodes))
    
    def build_model(self):
        """This is the entry point to the code that loads the NSD from the Project Repository.
        """
        self.log.info("Building model.\n simhome=%s\n sim_root=%s", self.simhome, self.sim_root)

        reader = NSDReader()
        self.nsd = reader.read_nsd(self.datastore, self.sim_root['nsdid'], self.simhome)
       
        self.log.info("NSD model built")

    
    def validate(self):
        self.log.info("NSD validated")
        
    
    def open_file(self, path):
        return open(os.path.join(self.simhome, path), "a")
        

    def generate_code(self):        
        generate_castalia(self)
        self.generate_nodefile()


   
    

class NetworkMapper:

    def __init__(self, nsd_obj, jsonplan, json_project):
        self.nsd=nsd_obj
        self.json_plan=jsonplan
        self.json_project=json_project


    def extract_jsonfile_info(self):
        data={}
        data["RF_simulations"]=extract_jsonfile_arg(self.json_plan,"simulations")
        self.data=json.dumps(data)
