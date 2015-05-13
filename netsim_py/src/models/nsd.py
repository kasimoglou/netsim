'''
This module defines the netsim service data model, using SQLAlchemy ORM mappings.


Created on Sep 17, 2014

@author: vsam
'''

from models.mf import model, attr, ref, refs, ref_list, annotation_class
from models.json_reader import required, descend, ignore, json_name
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


##############################
#  Application: part of an NSD
##############################


@model
class SensorType:
    pwr_consuption = attr(float)  # energy consumed per reading
    measurement = attr(str)  # quantity e.g. "temperature"
    max_sample_rate = attr(float)  #  samples per sec
    bias = attr(float)  # added to value
    drift = attr(float)  #  not used currently  (not used)
    noise_sigma = attr(float)  # sigma of gaussian noise added to value
    resolution = attr(float)  # sensed value is a multiple of this
    saturation = attr(float)  # the max. physical value measured
    hysterisis = attr(float)  # delay in sensor measuring change (not used)
    sensitivity = attr(float)  # the minimum physical value measured


# This type is used for Node coordinates (corresponds to PLNxxxx coord. triplet)
Position = namedtuple('Position', ('lat', 'lon', 'alt'))


@model
class MoteType:
    # node type name
    name = attr(str)

    # all nodes of this type
    nodes = refs()

    # The application code run by this mote. For now this is a string. 
    code = attr(str)

    #
    # Mote components
    # 

    sensors = attr(list)  # of SensorType objects

    # resources
    ram_size = attr(float)  # in kbytes
    flash_size = attr(float)  # in kbytes
    flash_write_cost = attr(float, nullable=True)
    flash_read_cost = attr(float, nullable=True)
    image_size = attr(float, nullable=True)

    initial_energy = attr(float)
    baseline_node_power = attr(float)


    #
    # Communication
    #

    mac = attr(str)
    radio = attr(str)
    routing = attr(str)


@model
class Mote:
    """A mote represents a wireless sensor, gateway, or other element in the network.
    """

    def __init__(self, network, moteType):
        self.network = network
        self.moteType = moteType

    # node id
    node_id = attr(str, nullable=False, default=None)

    # the node type determines the hardware used
    moteType = ref(inv=MoteType.nodes)

    #Mote role (ROOT or MOTE)
    moteRole = attr(str, nullable=False, default=None)

    # position of the node in relative coordinates
    position = attr(Position)

    rf_antenna_conf=attr(object)

    elevation= attr(float, nullable=False, default=None)

    rx_threshold= attr(float, nullable=False, default=None)

    # the Network object
    network = ref()


@model
class RFsimulation:
    def __init__(self, network):
        self.network = network

    # the Network object
    network = ref()
        


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

    RF_simulations = refs(inv=RFsimulation.network)


#
#  Parameters object
#
@model
class Parameters:
    nsd = ref()

    # The time reached when the simulation terminates (sec)
    sim_time_limit = attr(float)
    required(sim_time_limit)

    # Simulation time resolution exponent, The default is -9 (nanosec)
    simtime_scale = attr(int, default=-9)

    # CPU time limit, simulation stops when reached. The default is no limit.
    cpu_time_limit = attr(int, default=None)




######################################
#
#  The main NSD object
#
######################################


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
    #  Parameters
    #

    parameters = ref(inv=Parameters.nsd)
    descend(parameters)

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


    #
    # Environment
    #

    environment = ref(inv=Environment.nsd)

    #
    # Application
    #

    network = ref(inv=Network.nsd)
    EPSG=attr(str,nullable=False)
    networkId=attr(str,nullable=False)

    #
    # Statistics
    #
    plots = attr(list)
    
        
    
@model
class Plan:
    nsd = ref()

    name = attr(str, nullable=False)
    NodePosition= attr(list)
    numOfNodes=attr(int,nullable=False)
    numOfRoots=attr(int,nullable=False)
    numOfNidNodes=attr(int,nullable=False)

@model 
class Project:
    nsd = ref()

