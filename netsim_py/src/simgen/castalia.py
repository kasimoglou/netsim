'''
Created on Oct 14, 2014

@author: vsam
'''

import os.path
import json
import logging

from models.project_repo import NS_NODEDEF, NS_COMPONENT

from models.json_reader import JSONReader, repository
from simgen.validation import *

from models.mf import Attribute
from simgen.utils import docstring_template
from .castaliagen import generate_castalia

from models.nsd import NSD, Network, Mote, Position, Plan, Project,\
    CastaliaEnvironment, VectorlEnvironment, NodeDef, ConnectivityMatrix,\
    NsNodeDef, Sensor, MoteType, RadioDevice

from datavis.output_handler import validate_output

logger = logging.getLogger('codegen')

class NSDReader(JSONReader):
    """This class implements a text2model transformation:
    Given a datastore, it constructs an NSD model for the application.
    
    Subclassing this class, allows us to treat different "text schemas"  
    """
    def __init__(self, gen):
        self.gen = gen
        self.datastore = gen.datastore

    def read_nsd(self, nsd_id, simhome):
        '''
        Read an nsd and download all other linked information.
        All downloaded json objects are saved in the simulation home.

        Return the nsd object on wchich all the information is linked.
        '''
        nsd = NSD()
        self.nsd=nsd
        self.simhome=simhome
        # get nsd

        with Context(stage='Analyzing NSD'):
            nsd_json = self.read_object(nsd_id, nsd)
            self.create_jsonfile(nsd_json, "nsd.json")

            # add the environment spec
            nsd.environment = self.create_environment(nsd_json)

        nsd.plan = Plan()
        nsd.project = Project()

        #read Couchdb json files
        plan_json = {}
        with Context(stage='Analyzing plan'):
            if not hasattr(nsd, 'plan_id'):
                fatal("There is no plan for this NSD. Aborting.")
            plan_json = self.read_object(nsd.plan_id, nsd.plan)
            self.create_jsonfile(plan_json, "plan.json")

        project_json = {}
        with Context(stage='Analyzing project info'):
            if not hasattr(nsd, 'project_id'):
                fail("There is no project for the NSD.")
            project_json = self.read_object(nsd.project_id, nsd.project)
            self.create_jsonfile(project_json, "project.json")

        # Read nodedef objects
        nodeDefOids = {n.nodeTypeId for n in nsd.plan.NodePosition}
        logger.debug("Collected nodeDef objects: %s", nodeDefOids )

        self.nodeDefs = {oid: NodeDef() for oid in nodeDefOids}

        nodeDefJson = {}
        for oid in nodeDefOids:
            # Get the nodedef from the plan
            with Context(stage='Analyzing node type %s'%oid):
                nodeDefJson[oid] = self.read_object(oid, self.nodeDefs[oid])
            # Get the mapped ns_nodedef
            with Context(stage="Mapping simulation component for node type %s" % oid):
                self.get_ns_nodedef(self.nodeDefs[oid])


        self.create_jsonfile(nodeDefJson, "nodedefs.json")
        nsd.nodedefs = set(self.nodeDefs.values())

        # read connectivity matrix, if it exists
        if ('_attachments' in plan_json and 
             'connectivityMatrix.json' in plan_json['_attachments']):
            with Context(stage="Analyzing connectivity"):
                cm = nsd.plan.connectivityMatrix = ConnectivityMatrix()
                cm_json = self.read_object((plan_json,'connectivityMatrix.json'), cm)
                self.create_jsonfile(cm_json, "connectivityMatrix.json")

        # Create network model
        self.create_network()

        return nsd



    def get_ns_nodedef(self, nodedef):
        # Get by query the id of the object
        oid = nodedef._id
        try:
            ns_nodedef_json = self.datastore.get_by(NS_NODEDEF, 'by_nodeLib_id', oid)
        except Exception as e:
            print("Exception in get_by",e)
            logger.exception("In get_ns_nodedef oid=%s",oid)

            fail("Failed to map node type for %s in the library." % oid)

        # We did not find a mapping
        if ns_nodedef_json is None:
            warn("We did not find a mapping for node type %s", oid)
            return

        # create the object
        ns = NsNodeDef()
        nodedef.ns_nodedef = ns

        # Now read the ns nodedef from the library
        self.populate_modeled_instance(ns, ns_nodedef_json)

        # now, read the components into the attributes
        for attr in ('routing', 'mac'):
            if hasattr(ns, attr):
                oid = getattr(ns, attr)
                comp_json = self.datastore.get(NS_COMPONENT, oid)
                setattr(ns, attr, comp_json)

        # read the sensor array
        if hasattr(ns, 'sensors'):
            if len(ns.sensors)>5:
                fail("Too many sensors, at most five sensors per device are allowed")
            for i in range(len(ns.sensors)):
                sens_oid = ns.sensors[i]
                sens = Sensor()
                self.read_component(sens_oid, sens)
                ns.sensors[i] = sens
        else:
            warn("There is no sensor specification.")

        # read the mote type
        if hasattr(ns, 'mote'):
            mote_type = MoteType()
            self.read_component(ns.mote, mote_type)
            ns.mote = mote_type
        else:
            warn("There is no mote specification.")

        # read the radio spec
        if hasattr(ns, 'radio'):
            radio = RadioDevice()
            self.read_component(ns.radio, radio)
            ns.radio = radio
        else:
            warn("There is no radio specification.")


    def read_component(self, oid, obj):
        '''
        Read library component 'oid' from the repository, and populate model 'obj'.
        '''
        try:
            entity = repository.get(obj.__class__).entity
        except ValueError:
            fail("It was not possible to determine the repository entity for %s",obj.name)

        try:
            # read parameters
            json_obj = self.datastore.get(entity, oid)
        except Exception as e:
            fail("Failed to read %s with id='%s' from the project repository." % (entity.name, oid))

        try:
            self.populate_modeled_instance(obj, json_obj['parameters'])
        except Exception as e:
            logger.error("Failure in populate_modeled_instance(%s, %s)", obj, json_obj, exc_info=1)
            fail("Failed to analyze %s with id='%s'." % (entity.name, oid))

        logger.debug("%s=\n%s", entity.name, json.dumps(json_obj, indent=4))
        return json_obj


    def read_object(self, oid, obj):
        '''
        Read object oid from the repository, and populate model 
        object obj.
        '''
        try:
            entity = repository.get(obj.__class__).entity
        except ValueError:
            fail("It was not possible to determine the repository entity for %s",obj.name)

        try:
            # read parameters
            json_obj = self.datastore.get(entity, oid)
        except Exception as e:
            fail("Failed to read %s with id='%s' from the project repository." % (entity.name, oid))

        try:
            self.populate_modeled_instance(obj, json_obj)
        except Exception as e:
            logger.error("Failure in populate_modeled_instance(%s, %s)", obj, json_obj, exc_info=1)
            fail("Failed to analyze %s with id='%s'." % (entity.name, oid))

        logger.debug("%s=\n%s", entity.name, json.dumps(json_obj, indent=4))
        return json_obj

    def create_jsonfile(self, jsondata, filename):
        '''
        Creates a jsonfile with the jsondata in simhome
        '''
        with open(filename, 'w') as outfile:
            json.dump(jsondata, outfile)


    def create_environment(self, nsd_json):
        '''
        Create the correct environment spec in the nsd.
        '''
        if 'environment' not in nsd_json:
            fail('The NSD does not have an environment specification')
        env_json = nsd_json['environment']

        if 'type' not in env_json:
            fail('The NSD environment type is missing')

        if env_json['type']=='castalia':
            env = CastaliaEnvironment()
        elif env_json['type']=='vectorl':
            env = VectorlEnvironment()
        else:
            fail("The NSD contains an unknown environment type: %s" % env_json[type])
        self.populate_modeled_instance(env, env_json)
        self.nsd.environment = env


    def create_network(self):
        '''
        Adjust the data read into the NSD, before returning.
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

    def build_model(self):
        """
        This is the entry point to the code that loads the NSD from the Project Repository.
        """
        inform("Building model.")
        logger.debug("simhome=%s   sim_root=%s", self.simhome, self.sim_root)

        with Context(stage='Building network model') as build:
            reader = NSDReader(self)
            self.nsd = reader.read_nsd(self.sim_root['nsdid'], self.simhome)
        if build.success:
            inform("Network model built.")
        else:
            fatal("""Building the network model from information in the \
 project repository has failed. \
 Cannot continue with the generation. The simulation has failed.""")

    def validate(self):
        validate_output()
        inform("NSD validated.")
        
    
    def generate_code(self):        
        generate_castalia(self)
        inform("Simulation generated successfully.")


