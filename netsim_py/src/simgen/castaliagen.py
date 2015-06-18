
import os.path, logging, json
from runner.config import castalia_path, omnetpp_path

from simgen.validation import Context, fail, fatal, inform, warn, add_context
from models.nsd import *
from models.castalia_sim import *
from models.mf import Attribute
from simgen.utils import docstring_template
from simgen.datastore import context
import pyproj
import numpy as np

logger = logging.getLogger('codegen')

def generate_castalia(gen):
    '''
    Main entry routine for generating a castalia simulation from the NSD
    '''

    # generate the simulation
    cmb = CastaliaModelBuilder(gen)
    cmb.transform()
    m2t_castalia_model(gen, cmb.cm)

    # generate additional files
    with gen.output_file("executor.mak") as m:
        m.write(makefile(cmb))

    logger.debug("Code generated from NSD")


def copy_json_params(module, jsobj):
    for key in jsobj:
        if key not in ('_id', '_rev', 'type', 'moduleType','name'):
            module.set(key, jsobj[key])


class CastaliaModelBuilder:
    '''
    A class containing the logic to transform an NSD to a castalia model.
    This is an M2M transformation.
    '''

    def __init__(self, gen):
        # the inputs
        self.gen = gen
        self.nsd = gen.nsd

        # The castalia model to build
        self.cm = CastaliaModel()

        # The [General] section
        self.opp = General(self.cm)


    def transform(self):
        '''
        Main routine.
        '''

        with Context(stage='Initialize generation'):
            self.init_omnetpp_general()

        with Context(stage='Create simulated network'):
            self.create_network()

        for nodeType in self.cm.nodeTypes:
            with Context(stage='Process node type %s' % nodeType.nodeDef.name):
                self.create_node_type(nodeType)

        with Context(stage='Create environment simulation'):
            self.create_environment()

        with Context(stage='Parameterize wireless channel'):
            self.create_wireless_channel()

        with Context(stage='Configure simulation'):
            self.add_omnetpp_sections()


    def init_omnetpp_general(self):
        '''
        Create Omnetpp model from NSD
        '''
        self.opp.sim_time_limit = self.nsd.parameters.sim_time_limit
        self.opp.simtime_scale = self.nsd.parameters.simtime_scale
        self.opp.cpu_time_limit = self.nsd.parameters.cpu_time_limit
        self.opp.castalia_path = castalia_path()

    def add_omnetpp_sections(self):
        # Add network to [General]
        self.opp.modules.append(self.cm.network)

        # Add nodes section
        nodeSection = Section(self.cm, 'Nodes')
        nodeSection.modules.append(self.nodes)

        # Add sections for node types
        for nodeType in self.cm.nodeTypes:
            s = Section(self.cm, 'NodeType_%s '% nodeType.nodeDef.code)
            nodeType.section = s
            s.modules.append(nodeType.nodes)
        # make the names of node types legal!


        # Add section for HiL
        hil_section = Section(self.cm, 'HiL')

        # Final, main section
        ext = [hil_section]+[nt.section for nt in self.cm.nodeTypes]+[nodeSection]
        self.main_section = Section(self.cm, 'Main', extends=ext)


    def create_network(self):
        '''
        Scan through the NSD and analyze into pieces for further
        processing
        '''

        # Configure network module. This must be done first!
        net = Network(None, 'SN')
        self.cm.network = net


        # filter the node types, excluding NIDs
        # separate the motes into types and assign ranges
        pos = 0
        for nodeDef in self.nsd.nodedefs:
            # skip NIDs
            if nodeDef.nature == 'NID':
                continue
            size = len(nodeDef.motes)
            index = slice(pos, pos+size)
            pos += size
            # create the type
            NodeType(self.cm, nodeDef, index)
        net.numNodes = pos



        # Configure node modules
        self.nodes = net.base()
        for nodeType in self.cm.nodeTypes:
            # assign numbers to the nodes
            num = nodeType.index.start
            for mote in nodeType.nodeDef.motes:
                # create node module
                node = Node(self.nodes, 'node', num)
                num += 1
                node.name = mote.node_id
                node.mote = mote        

        assert net.numNodes == len(self.nodes.submodules)

        # Create the nodemap.json
        nodemap = []
        for node in self.nodes.submodules:
            mapped_node = {
                "simid": node.index,
                "nodeid": node.name
            }
            nodemap.append(mapped_node)
        with open("nodemap.json", 'w') as outfile:
            json.dump({ "nodes": nodemap }, outfile)


        # adjust node coordinates and compute Area Of Interest
        AOI = self.compute_positions(self.nodes.submodules)

        # init parameters in network
        net.field_x = AOI[0]
        net.field_y = AOI[1]
        net.field_z = AOI[2]

        return net
        

    def compute_positions(self, node_modules):
        '''
        Takes a collection of Node modules and adorns them with coordinates.
        Returns the area of interest.
        '''
        #
        # create Proj objects for mapping
        #

        # all PT coordinates in epsg 4326
        from_proj = pyproj.Proj(init='epsg:4326')

        # for output coordinates, create an appropriate UTM projection
        to_proj = pyproj.Proj(proj='utm', 
            lon_0=node_modules[0].mote.position.lon, 
            ellps='WGS84')

        # make array of positions, keep track of the correspondence to nodes
        node_array = [x for x in node_modules]
        all_pos = np.zeros((len(node_array), 3))
        i = 0
        for n in node_array:
            x,y = pyproj.transform(from_proj, to_proj, 
                        n.mote.position.lon, n.mote.position.lat)
            z = n.mote.position.alt + n.mote.elevation
            all_pos[i,:] = np.array([x,y,z])
            i += 1

        # rebase coordinates to the (0,0)-(P,Q) rectangle, 
        # with a buffer zone of width B
        B = 5.0
        bufzone = np.array([B, B, 0.0])
        min_pos = np.min(all_pos, axis=0) - bufzone

        final_pos = all_pos - min_pos

        # set node parameters
        for i in range(len(node_array)):
            node = node_modules[i]
            node.xCoor = final_pos[i][0]
            node.yCoor = final_pos[i][1]
            node.zCoor = final_pos[i][2]

        aoi = np.max(final_pos, axis=0) + bufzone

        return aoi



    def create_environment(self):
        '''
        Configure the environment simulation.
        '''
        # TBD: make this adhere to model
        net = self.cm.network
        net.numPhysicalProcesses = 1
        net.physicalProcessName = 'CustomizablePhysicalProcess'



    def create_wireless_channel(self):
        '''
        Configure the wireless channel.
        '''
        pass
        # use the connectivity matrix


    def create_node_type(self, nodeType):
        '''
        Configure the node type simulation modules
        '''
        self.config_application(nodeType)
        self.config_communication(nodeType)
        self.config_resources(nodeType)
        self.config_sensors(nodeType)



    def config_communication(self, nodeType):
        '''
        Configure the communication stack.
        '''
        radio = Radio(nodeType.comm,'Radio')
        radio.RadioParametersFile = "../Parameters/Radio/CC2420.txt"
        radio.symbolsForRSSI = 8


    def config_application(self, nodeType):
        '''
        Configure application logic.
        '''
        nodeType.nodes.ApplicationName = "ConnectivityMap"


    def config_resources(self, nodeType):
        '''
        Configure resources.
        '''
        rman = nodeType.nodes.submodule('ResourceManager')
        nsdef =  nodeType.nodeDef.ns_nodedef 
        if nsdef is not None:
            rman_json = nsdef.ResourceManager
            copy_json_params(rman, rman_json)


    def config_sensors(self, nodeType):
        '''
        Configure sensors.
        '''
        pass


##################################################
#
# M2T transform:  CastaliaModel 
# 
##################################################

def m2t_castalia_model(gen, cm):
    '''
    Create the simulation files.
    '''
    generate_omnetpp(gen, cm)


def generate_omnetpp(gen, cm):
    '''
    Generate the omnetpp.ini file.
    '''
    logger.debug("Generating omnetpp.ini")    
    with gen.output_file("omnetpp.ini") as omnetpp:
        # start with preamble
        preamble = omnetpp_preamble(cm)
        omnetpp.write(preamble)

        # iterate over the sections
        for section in cm.omnetpp:
            # print section header
            header = omnetpp_section_header(section)
            omnetpp.write(header)
            for m in section.modules:
                generate_omnetpp_for_module(omnetpp, m)



def generate_omnetpp_for_module(omnetpp, m):
    # first, iterate over module parameters
    mpath = m.full_name

    for pname, pvalue in m.all_parameters():
        omnetpp.write(omnetpp_module_param(m, mpath, pname,pvalue))

    # now, iterate over submodules
    for sm in m.submodules:
        generate_omnetpp_for_module(omnetpp,sm)



#
#  omnetpp.ini
#

@docstring_template
def omnetpp_module_param(mod, modpath, pname, pvalue):
    """\
% if pvalue is not None:
{{modpath}}.{{pname}} = {{! pvalue}}
% end"""
    if isinstance(pvalue, str):
        pvalue = '"%s"' % pvalue
    return locals()


@docstring_template
def omnetpp_section_header(section):
    """
#
# section 
#
% if name:
[Config {{! name}}]
% end
% if extends:
extends = {{! ', '.join(s.name for s in extends) }}
% end


"""
    name = section.name
    extends = section.extends
    return locals()


@docstring_template
def omnetpp_preamble(cm):
    """
#
#  Generated by the netsim generator.
# 

[General]

# ==========================================================
# The main Castalia.ini file is included inline (!)
# ==========================================================

cmdenv-express-mode = true
cmdenv-module-messages = true
cmdenv-event-banners = false
cmdenv-performance-display = false
cmdenv-interactive = false

ned-path = {{param.castalia_path}}/src

network = SN    # this line is for Cmdenv

output-vector-file = Castalia-statistics.vec
output-scalar-file = Castalia-statistics.sca

# 11 random number streams (or generators as OMNeT calls them)
num-rngs = 11 

# ===========================================================
# Map the 11 RNGs streams with the various module RNGs. 
# ==========================================================

{{!NET}}.wirelessChannel.rng-0        = 1     # used to produce the random shadowing effects
{{!NET}}.wirelessChannel.rng-2        = 9 # used in temporal model
                                    
{{!NET}}.node[*].Application.rng-0        = 3 # Randomizes the start time of the application
{{!NET}}.node[*].Communication.Radio.rng-0    = 2 # used to decide if a receiver, with X probability.
                        # to receive a packet, will indeed receive it

{{!NET}}.node[*].Communication.MAC.rng-0  = 4 # Produces values compared against txProb
{{!NET}}.node[*].Communication.MAC.rng-1  = 5 # Produces values between [0 ....  randomTxOffset]

{{!NET}}.node[*].ResourceManager.rng-0    = 6 # Produces values of the clock drift of the CPU of each node
{{!NET}}.node[*].SensorManager.rng-0      = 7 # Produces values of the sensor devices' bias
{{!NET}}.node[*].SensorManager.rng-1      = 8 # Produces values of the sensor devices' noise

{{!NET}}.physicalProcess[*].rng-0         = 10    # currently used only in CarsPhysicalProcess

{{!NET}}.node[*].MobilityManager.rng-0    = 0 # used to randomly place the nodes


#  End of Basic config

sim-time-limit = {{param.sim_time_limit}}s
simtime-scale = {{param.simtime_scale}}
% if param.cpu_time_limit is not None:
cpu-time-limit = {{param.cpu_time_limit}}s
% end

"""
    NET = cm.network.full_name
    param = cm.omnetpp[0]
    return locals()



"""

sim-time-limit = 100s

{{!NET}}.field_x = 30                                 # meters
{{!NET}}.field_y = 30                                 # meters

# Specifying number of nodes and their deployment
{{!NET}}.numNodes = 9
{{!NET}}.deployment = "3x3"

# Removing variability from wireless channel
{{!NET}}.wirelessChannel.bidirectionalSigma = 0
{{!NET}}.wirelessChannel.sigma = 0

# Select a Radio and a default Tx power
{{!NET}}.node[*].Communication.Radio.RadioParametersFile = "../Parameters/Radio/CC2420.txt"
{{!NET}}.node[*].Communication.Radio.TxOutputPower = "-5dBm"

# Using connectivity map application module with default parameters
{{!NET}}.node[*].ApplicationName = "ConnectivityMap"

[Config varyTxPower]
{{!NET}}.node[*].Communication.Radio.TxOutputPower = ${TXpower="0dBm","-1dBm","-3dBm","-5dBm"}

[Config varySigma]
{{!NET}}.wirelessChannel.sigma = ${Sigma=0,1,3,5}

"""



@docstring_template
def makefile(cmb):
    """\
# 
# This is an automatically generated makefile
#

SIMHOME={{! simhome}}
OMNETPP_PATH={{! opp_path}}
CASTALIA_PATH={{! cast_path}}

PATH:=/bin:/usr/bin:$(OMNETPP_PATH)/bin
LD_LIBRARY_PATH=$(OMNETPP_PATH)/lib

SIMEXEC=simexec

.PHONY: all compile run

all: compile run

compile:
\tln -s $(CASTALIA_PATH)/makefrag.inc makefrag
\topp_makemake -f -r --deep -o $(SIMEXEC) -u Cmdenv -P $(SIMHOME) -M release -X./Simulations -X./src -L$(CASTALIA_PATH) -lcastalia
\t$(MAKE)

run:
\t./$(SIMEXEC) --cmdenv-output-file=simout.txt -c Main

"""
    cast_path = castalia_path()
    opp_path = omnetpp_path()
    simhome = context.fileloc
    return locals()
