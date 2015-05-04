'''
Created on Oct 14, 2014

@author: vsam
'''

import os.path
import json
from models.nsd import NSD
from models.mf import Attribute
from simgen.utils import docstring_template
from .castaliagen import generate_castalia


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
        if json_field in json:
        
            tval = transform_value(attr, json[json_field])
            setattr(model, attr.name, tval)



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
        """
        planid=nsd_obj["plan_id"]
        self.plan=datastore.get_plan(planid)
        populate_modeled_instance(nsd, self.plan)
        
        projectid=nsd_obj["project_id"]
        self.project=datastore.get_project(projectid)
        populate_modeled_instance(nsd, self.project)
        """
        return nsd
     
    def read_plan(self, datastore, nsd):
        planid=nsd.plan_id
        plan=datastore.get_plan(planid)
        populate_modeled_instance(nsd, plan)
        return plan
   
        
        

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
        with self.node_file("nodefile.txt") as nodefile:
            nodes = self.extract_nodeinfo(self.plan)
            for node in nodes:
                nodefile.write(str(node))
    
    def build_model(self):
        """This is the entry point to the code that loads the NSD from the Project Repository.
        """
        self.log.info("Building model.\n simhome=%s\n sim_root=%s", self.simhome, self.sim_root)

        reader = NSDReader()
        self.nsd = reader.read_nsd(self.datastore, self.sim_root['nsdid'], self.simhome)
        self.plan= reader.read_plan(self.datastore, self.nsd)
        self.log.info("NSD model built")

    
    def validate(self):
        self.log.info("NSD validated")
        
    
    def node_file(self, path):
        return open(os.path.join(self.simhome, path), "a")
        

    def generate_code(self):        
        generate_castalia(self)
        self.generate_nodefile()


    def extract_nodeinfo(self, data):
        nodes=[]
        for k,v in data.items():
                if k=="nodeId":
                    nodes.append=v
        return nodes