'''
This module defines the netsim service data model, using SQLAlchemy ORM mappings.


Created on Sep 17, 2014

@author: vsam
'''

from models.mf import model, attr, ref, refs, ref_list, annotation_class
from models.json_reader import repository, required, descend, \
    ignore, json_name, json_filter
import models.project_repo as prm
from collections import namedtuple
from enum import Enum
from numbers import Number



##############################
# Environment: part of an NSD
##############################


@model
class Environment:
    '''
    This class encapsulates the specification of the environment for an NSD.
    Environment refers to the physical quantities sensed by the sensors in the
    WSN.
    '''
    nsd = ref()

    type = attr(str, nullable=False)
    required(type)

@model
class CastaliaEnvironment(Environment):
    pass

@model
class VectorlEnvironment(Environment):
    vectorl_id = attr(str, nullable=False)
    json_name('vectrol_id')(vectorl_id)
    required(vectorl_id)


##############################
#  Application: part of an NSD
##############################


@repository(prm.NS_COMPONENT)
@model
class RadioDevice:
    """
    Models a radio device.
    """
    RadioParametersFile = attr(str, default=None)
    mode = attr(str, default="")
    state = attr(str, default="RX")
    TxOutputPower = attr(str, default="")
    sleepLevel = attr(str, default="")
    carrierFreq = attr(float, default=2400.0)
    collisionModel = attr(int, default=2)
    CCAthreshold = attr(float, default=-95.0)
    symbolsForRSSI = attr(int, default=8)
    carrierSenseInterruptEnabled = attr(bool, default=False)
    bufferSize = attr(int, default=16)
    maxPhyFrameSize = attr(int, default=1024)
    phyFrameOverhead = attr(int, default=6)


@repository(prm.NS_COMPONENT)
@model
class Sensor:
    """
    Models a sensor device.
    """
    pwr_consuption = attr(float)  # energy consumed per reading
    sensor_type = attr(str)  # quantity e.g. "temperature"
    max_sample_rate = attr(float)  #  samples per sec
    bias = attr(float)  # added to value
    drift = attr(float)  #  not used currently  (not used)
    noise_sigma = attr(float)  # sigma of gaussian noise added to value
    resolution = attr(float)  # sensed value is a multiple of this
    saturation = attr(float)  # the max. physical value measured
    hysterisis = attr(float)  # delay in sensor measuring change (not used)
    sensitivity = attr(float)  # the minimum physical value measured


@repository(prm.NS_COMPONENT)
@model
class MoteType:
    """
    Models the mote device.
    """

    # resources
    ramSize = attr(float, nullable=True)  # in kbytes
    flashSize = attr(float, nullable=True)  # in kbytes
    flashWriteCost = attr(float, nullable=True)
    flashReadCost = attr(float, nullable=True)
    imageSize = attr(float, nullable=True)

    initialEnergy = attr(float, default=18720.0)
    baselineNodePower = attr(float, default=6.0)



# This type is used for Node coordinates (corresponds to PLNxxxx coord. triplet)
Position = namedtuple('Position', ('lat', 'lon', 'alt'))


@model
class FunctionalBlock:
    blockDefId = attr(str)
    blockName = attr(str)
    blockCode = attr(str)
    isReprogrammable = attr(str)
    isConfigurable = attr(str)
    nature = attr(str)
    noInstances = attr(int)
    blockInstanceId = attr(int)

    nodeType = ref()

@repository(prm.NODEDEF)
@model
class NodeDef:
    """
    The Planning Tool's node definition.
    """

    # some code word
    code = attr(str)

    # human-readable
    description = attr(str)

    # NODE/ROOT/NID
    nature = attr(str, nullable=False)
    required(nature)

    functionalBlocks = refs(inv=FunctionalBlock.nodeType)
    descend(functionalBlocks)

    name = attr(str, nullable=False)

    motes = refs()
    nsd = ref()

    ns_nodedef = ref()

    # couch entities
    _id = attr(str)
    _rev = attr(str)




@repository(prm.NS_NODEDEF)
@model
class NsNodeDef:
    """
    The NetSim library node definition.
    """

    nodedef = ref(inv=NodeDef.ns_nodedef)

    mote = attr(object)
    sensors = attr(list)
    routing = attr(object)
    mac = attr(object)
    radio = attr(object)

    # couch entities
    _id = attr(str)
    _rev = attr(str)



@model
class Mote:
    """
    A mote represents a wireless sensor, gateway, 
    or other element in the network.
    """
    # node id
    node_id = attr(str, nullable=False, default=None)
    required(node_id)
    json_name('nodeId')(node_id)


    # the node type determines the hardware used
    nodeTypeId = attr(str)
    required(nodeTypeId)
    nodeType = ref(inv=NodeDef.motes)

    #Mote role (ROOT or MOTE)
    moteRole = attr(str, nullable=False, default=None)
    required(moteRole)
    json_name('nodeType')(moteRole)

    # position of the node in relative coordinates
    position = attr(Position)
    json_name('coordinates')(position)
    required(position)
    json_filter(lambda coord: Position(*(float(c) for c in coord)))(position)

    rf_antenna_conf=attr(object)

    elevation= attr(float, nullable=False, default=0.0)
    json_name('elevOfGround')(elevation)

    rx_threshold= attr(float, nullable=False, default=None)
    json_name('RXthreshold')(rx_threshold)    

    # the Network object
    network = ref()

    # The plan that this is read initially from
    plan = ref()



@model
class Network:
    """The object describing a Wireless Sensor Network
    """

    def __init__(self, nsd):
        self.nsd = nsd

    # the NSD
    nsd = ref()

    # All nodes
    motes = refs(inv=Mote.network)

    def find_mote(self, node_id):
        """
        Return a mote for the given node_id, or None if no such mote exists.
        """
        for mote in self.motes:
            if mote.node_id == node_id:
                return mote
        return None


#
#  Parameters object
#
@model
class Parameters:
    "NSD parameters"

    nsd = ref()

    # The time reached when the simulation terminates (sec)
    sim_time_limit = attr(float)
    required(sim_time_limit)

    # Simulation time resolution exponent, The default is -9 (nanosec)
    simtime_scale = attr(int, default=-9)

    # CPU time limit, simulation stops when reached. The default is no limit.
    cpu_time_limit = attr(int, default=None)



@model
class HiL:
    "The nsd configuration for HiL simulation"

    nsd = ref()
    node1 = attr(str, nullable=False)
    node2 = attr(str, nullable=False)


######################################
#
#  The main NSD object
#
######################################


@repository(prm.NSD)
@model
class NSD:
    '''
    Network Simulation Descriptor
    
    This class encapsulates a model to be simulated. It does not contain runtime aspects
    of the simulation execution itself, such as simulation platform, execution engine etc. 
    
    An NSD has 4 parts:

    parameters -  a descriptor object containing simulation-related parameters

    environment - a descriptor object used to define the simulation of the environment,
                such as the measurements of the sensors
                
    application -   a descriptor object defining the application simulated (network structure,
                node types, application logic etc)                
    
    statistics - a descriptor object specifying the results generated from simulations
            
    '''

    #
    # DPCM platform attributes
    #

    plan_id = attr(str, nullable=False)
    required(plan_id)

    project_id = attr(str, nullable=False)
    required(project_id)

    name = attr(str, nullable=False)
    required(name)

    userId=attr(str,nullable=False)
    
    plan = ref()
    project = ref()
    nodedefs = refs(inv=NodeDef.nsd)


    #
    # Application
    #

    # network object
    network = ref(inv=Network.nsd)

    hil = ref(inv=HiL.nsd)
    descend(hil)

    #
    #  Parameters
    #

    parameters = ref(inv=Parameters.nsd)
    descend(parameters)


    #
    # Environment
    #

    environment = ref(inv=Environment.nsd)


    #
    # Statistics
    #
    plots = attr(list)
    
    # couch entities
    _id = attr(str)
    _rev = attr(str)
        
    
@repository(prm.PLAN)
@model
class Plan:
    " A PT plan object "
    nsd = ref(inv=NSD.plan)

    name = attr(str, nullable=False)

    NodePosition= refs(inv=Mote.plan)
    descend(NodePosition)

    # numbers
    numOfNodes=attr(int,nullable=False)
    numOfRoots=attr(int,nullable=False)
    numOfNidNodes=attr(int,nullable=False)

    # units of measurement
    UOMs = attr(object)

    connectivityMatrix = ref()

    # couch entities
    _id = attr(str)
    _rev = attr(str)


@repository(prm.PLAN)
@model
class ConnectivityMatrix:
    "The Connectivity matrix from the topology simulator."
    plan = ref(inv=Plan.connectivityMatrix)

    rfSimId = attr(str)

    connectivity = ref_list()
    descend(connectivity)

@model
class Channel:
    "A channel is an entry to the connectivity matrix"
    cm = ref(inv=ConnectivityMatrix.connectivity)

    channelId = attr(int)
    required(channelId)

    nodeId1 = attr(int)
    required(nodeId1)
    RSSnodeId1 = attr(float)
    required(RSSnodeId1)
    TXpowerNodeId1 = attr(float)
    required(TXpowerNodeId1)

    nodeId2 = attr(int)
    required(nodeId2)
    RSSnodeId2 = attr(float)
    required(RSSnodeId2)
    TXpowerNodeId2 = attr(float)
    required(TXpowerNodeId2)

    strengthDb = attr(float)
    required(strengthDb)


@repository(prm.PROJECT)
@model 
class Project:
    "The project object"

    nsd = ref(inv=NSD.project)

    # the owner of the project
    userId = attr(str)

    # a list of plans (strings)
    plans = attr(list)

    name = attr(str)

    # this is the EPSG used by the mapping tools, always a UTM srs
    EPSG = attr(str)

    # couch entities
    _id = attr(str)
    _rev = attr(str)

