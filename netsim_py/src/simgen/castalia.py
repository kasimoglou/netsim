'''
Created on Oct 14, 2014

@author: vsam
'''

import os.path
import json
from models.nsd import NSD, Network, Mote, MoteType, Position, RF_Antenna_conf, RFsimulation
from models.mf import Attribute
from simgen.utils import docstring_template
from .castaliagen import generate_castalia
from simgen.test_jsondata import test_read_plan, test_motedata
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
    def __init__(self):
        # array storing NodeDef objects 
        self.nodeinfo=[]


    def read_nsd(self, datastore, nsd_id, simhome):
        nsd = NSD()
        self.simhome=simhome
        # get nsd
        nsd_obj = datastore.get_nsd(nsd_id)
        
        # read parameters
        populate_modeled_instance(nsd, nsd_obj)
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
        planid=nsd.plan_id
        plan=datastore.get_plan(planid)
        populate_modeled_instance(nsd, plan)
        return plan

    #
    #Read the  project json file from CouchDb
    #  
    def read_project(self, datastore, nsd):
        projectid=nsd.project_id
        project=datastore.get_project(projectid)
        populate_modeled_instance(nsd, project)
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
        numOfNodes=int(self.nsd.numOfNodes)
        for i in range (0, numOfNodes):
            self.create_mote(self.plan['NodePosition'][i])
            #Read the NODEDEF object and store it to the nodeifo list
            nodedata=self.read_nodedef(datastore, self.plan['NodePosition'][i]['nodeTypeId'])
            nodedef=NodeDef(self.nsd, nodedata)
            self.nodeinfo.append(nodedef)
        self.read_rfsimulations(datastore, self.plan['simulations'])
        """
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
       
        #Extract arguments from json 
        metamodel = mote.__model_class__
        for attr in metamodel.attributes:
            if(attr.name =='node_id'):
                tval = transform_value(attr, data["nodeId"])
                setattr(mote, 'node_id', tval)
            elif (attr.name=='moteRole'):
                tval = transform_value(attr, data['nodeType'])
                setattr(mote, 'moteRole', tval)
            elif (attr.name=='position'):
                tval = transform_value(attr,(Position(float(data['coordinates'][0]), float(data['coordinates'][1]), float(data['coordinates'][2]))))
                setattr(mote, 'position', tval)
            elif (attr.name=='elevation'):
                tval = transform_value(attr, float(data['elevOfGround']))
                setattr(mote, 'elevation', tval) 
            elif (attr.name=='rx_threshold'):
                tval = transform_value(attr, float(data['RXthreshold']))
                setattr(mote, 'rx_threshold', tval)   
            elif (attr.name=='rf_antenna_conf'):
                tval = transform_value(attr,(RF_Antenna_conf(data['rfAntennaConf']['antennaTypeId'], data['rfAntennaConf']['anglePointer'], data['rfAntennaConf']['TXresistance'], data['rfAntennaConf']['TXpower'], data['rfAntennaConf']['TXpolarization'])))
                setattr(mote, 'rf_antenna_conf', tval)
        #test_motedata(mote)
            
        
        

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



    