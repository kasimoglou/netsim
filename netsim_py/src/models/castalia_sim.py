'''
This model describes the code base for a generated Castalia-based simulation.

Created on Oct 12, 2014

@author: vsam
'''

from models.mf import model, ref, refs, ref_list, attr, annotation_class
from collections import namedtuple
from models.nsd import *


def index_to_text(idx):
    '''
    This method prints an index (a number of a slice) into
    the grammar of omnet++ :   [3] or [3..6] or [*]
    '''
    if isinstance(idx, int):
        return "%d" % idx
    else:
        assert isinstance(idx, slice)
        p,q = slice.start, slice.stop
        if p is None and q is None:
            return "*"
        a = str(idx.start) if idx.start is not None else ""
        b = str(idx.stop-1) if idx.stop is not None else ""
        return "%s..%s" % (a,b)


@model
class CastaliaModule:
    # module tree
    parent = ref()
    submodules = ref_list(inv=parent)

    # The name and index of this submodule in the parent
    subname = attr(str, nullable=False)

    # the index can be a number or a range.
    index = attr(type=(int,slice), nullable=True, default=None)

    @property
    def full_name(self):
        if self.index is None:
            myname = self.subname
        else:
            myname = "%s[%s]" % (self.subname, index_to_text(self.index))

        if self.parent is None:
            return myname
        else:
            return '.'.join([self.parent.full_name, myname])

    def dummy(self, name, index):
        return CastaliaModule(self, name, index)

    def __init__(self, parent, name, index=None):
        self.parent = parent
        self.subname = name
        self.index = index




# an annotation for parameter attributes
Param = annotation_class('Param',[])()

# convenience declaration for annotated attributes
def parameter(type, **kwargs):
    return Param(attr(type=type, **kwargs))


@model
class Network(CastaliaModule):
    """
    int field_x = default (30);                     // the length of the deployment field
    int field_y = default (30);                     // the width of the deployment field
    int field_z = default (0);                      // the height of the deployment field (2-D field by default)

    int numNodes;                                           // the number of nodes

    string deployment = default ("");

    int numPhysicalProcesses = default (1);
    string physicalProcessName = default ("CustomizablePhysicalProcess");
    string debugInfoFileName = default ("Castalia-Trace.txt");
    """
    field_x = parameter(float)
    field_y = parameter(float)
    field_z = parameter(float)

    numNodes = parameter(int)
    numPhysicalProcesses = parameter(int)
    physicalProcessName = parameter(str)

@model
class WirelessChannel(CastaliaModule):
    """
    bool collectTraceInfo = default (false);
    bool onlyStaticNodes = default (true);          // if NO mobility, set it to true for greater efficiency 

    int xCellSize = default (5);            // if we define cells (to handle mobility)
    int yCellSize = default (5);            // how big are the cells in each dimension
    int zCellSize = default (1);

    double pathLossExponent = default (2.4);  // how fast is the signal strength fading
    double PLd0 = default (55);               // path loss at reference distance d0 (in dBm)
    double d0 = default (1.0);                // reference distance d0 (in meters)

    double sigma = default (4.0);  // how variable is the average fade for nodes at the same distance
                                   // from eachother. std of a gaussian random variable.

    double bidirectionalSigma = default (1.0);      // how variable is the average fade for link B->A if we know
                                                    // the fade of link A->B. std of a gaussian random variable

    string pathLossMapFile = default ("");          // describes a map of the connectivity based on pathloss
                                                    // if defined, then the parameters above become irrelevant

    string temporalModelParametersFile = default ("");      
                                    // the filename that contains all parameters for 
                                    // the temporal channel variation model

    double signalDeliveryThreshold = default (-100);        
                            // threshold in dBm above which, wireless channel module
                            // is delivering signal messages to radio modules of 
                            // individual nodes
    """
    pass


@model
class Node(CastaliaModule):
    '''
      //node location is defined by five parameters below
        double xCoor = default (0);
        double yCoor = default (0);
        double zCoor = default (0);
        double phi = default (0);
        double theta = default (0);
        
        double startupOffset = default (0);        //node startup offset (i.e. delay), in seconds 
        double startupRandomization = default (0.05);   //node startup randomisation, in seconds
        // Node will become active startupOffset + random(startupRandomization) 
        // seconds after the start of simulation

        string ApplicationName;                                                                         //the name of the implemented Application Module
        string MobilityManagerName = default ("NoMobilityManager");     //the name of the implemented Mobility Module
    '''
    xCoor = parameter(float)
    yCoor = parameter(float)
    zCoor = parameter(float)
    ApplicationName = parameter(str)

    name = attr(str, nullable=False)
    mote = attr(Mote, nullable=False)

@model
class ResourceManager(CastaliaModule):
    '''
        bool collectTraceInfo = default (false);
        double ramSize = default (0.0);                 //in kB
        double flashSize = default (0.0);               //in kB
        double flashWriteCost = default (0.0);  //per kB
        double flashReadCost = default (0.0);   //per kB
        double imageSize = default (0.0);   //the space that the OS (e.g. Contiki or TinyOS) occupies in the flash

        string cpuPowerSpeedLevelNames = default ("");
        string cpuPowerPerLevel = default (""); //spent energy per time unit
        string cpuSpeedPerLevel = default ("");
        int cpuInitialPowerLevel = default (-1);        // index for the cpuPowerLevels array
        double sigmaCPUClockDrift = default (0.00003);  // the standard deviation of the Drift of the CPU

        double initialEnergy = default (18720);
        // energy of the node in Joules, default value corresponds to two AA batteries
        // source http://www.allaboutbatteries.com/Energy-tables.html

        double baselineNodePower = default (6); // periodic energy consumption of node, in mWatts
        double periodicEnergyCalculationInterval = default (1000); // interval for energy calculation, in msec     
    '''
    initialEnergy = parameter(float)

@model
class SensorManager(CastaliaModule):
    '''
    bool collectTraceInfo = default (false);
    int numSensingDevices = default (1);            // how many sensing devices the node has 
                                                    // (has to be <= SensorNetwork.numPhysicalProcesses)

    string pwrConsumptionPerDevice = default ("0.02");

    string sensorTypes = default ("Temperature");   // Humidity OR Temperature OR Light

    string corrPhyProcess = default ("0");          //holds the indexes of the corresponding phy processes for
                                                    //each sensor (usually it should be : "0 1 2 3")

    string maxSampleRates = default ("1");          //number of samples per second for each sensor

    string devicesBias = default ("0.1");           //If the output signal is not zero when the measured property is zero

    string devicesDrift = default ("");             //If the output signal slowly changes independent of the 
                                                    //measured property
                                                                                            
    string devicesNoise = default ("0.1");          //random deviation of the signal that varies in time

    string devicesHysterisis = default ("");        //the sensor not instantly follows the change of the property 
                                                    //being measured and therefore involves the history of the 
                                                    //measured property

    string devicesSensitivity = default ("0");      //holds the minimum value which can be sensed by each sensing device.

    string devicesResolution = default ("0.001");   //holds the sensing resolution for each device 
                                                    //(the returned value will always be a multiple of 
                                                    //number, given here)
                                                                                                    
    string devicesSaturation = default ("1000");    //holds the saturation value for each sensing device
    '''
    numSensingDevices = parameter(int)
    pwrConsumptionPerDevice = parameter(str)
    sensorTypes = parameter(str)
    corrPhyProcess = parameter(str)
    maxSampleRates = parameter(str)
    devicesBias = parameter(str)
    devicesDrift = parameter(str)
    devicesNoise = parameter(str)
    devicesHysterisis = parameter(str)
    devicesSensitivity = parameter(str)
    devicesResolution = parameter(str)
    devicesSaturation = parameter(str)



@model
class Application(CastaliaModule):
    """
    string applicationID;
    bool collectTraceInfo;
    int priority;
    int packetHeaderOverhead;       // in bytes
    int constantDataPayload;        // in bytes
    """
    applicationID = parameter(str)
    packetHeaderOverhead = parameter(int)
    constantDataPayload = parameter(int)


@model
class Communication(CastaliaModule):
    """
    string MACProtocolName = default ("BypassMAC");
    string RoutingProtocolName = default ("BypassRouting");
    """
    MACProtocolName = parameter(str)
    RoutingProtocolName = parameter(str)

@model
class Radio(CastaliaModule):
    """
    string RadioParametersFile = default ("");      // variable points to the file that cointains most radio parameters

    string mode = default ("");     // we can choose a mode to begin with. Modes are defined in the
                                    // RadioParametersFile. Empty string means use the first mode defined

    string state = default ("RX");  // we can choose a radio state to begin with. RX and TX are always there.
                                    // according to the radio defined we can choose from a different set of sleep states

    string TxOutputPower = default ("");    // we can choose a Txpower to begin with. Possible tx power values 
                                            // are defined in the RadioParametersFile. Empty string means use 
                                            // the first tx power defined (which is also the highest)

    string sleepLevel = default ("");       // we can choose a sleep level which will be used when a transition to SLEEP state
                                            // is requested. Empty string means use first level defined (will usually be the fastest
                                            // and most energy consuming sleep state)

    double carrierFreq = default (2400.0);  // the carrier frequency (in MHz) to begin with.

    int collisionModel = default (2);       // 0-> No interference
                                            // 1-> Simple interference
                                            // 2-> Additive interefence
                                            // 3-> Advanced interference (not implemented)

    double CCAthreshold = default (-95.0);  // the threshold of the RSSI register (in dBm) 
                                            // were above it channel is NOT clear

    int symbolsForRSSI = default (8);
    bool carrierSenseInterruptEnabled = default (false);

    int bufferSize = default (16);  // in number of frames
    int maxPhyFrameSize = default (1024);   // in bytes
    int phyFrameOverhead = default (6);     // in bytes (802.15.4. = 6 bytes)
    """
    RadioParametersFile = parameter(str)
    mode = parameter(str)
    state = parameter(str)
    TxOutputPower = parameter(str)
    sleepLevel = parameter(str)
    carrierFreq = parameter(float)
    collisionModel = parameter(int)
    CCAthreshold = parameter(float)
    symbolsForRSSI = parameter(int)
    carrierSenseInterruptEnabled = parameter(bool)
    bufferSize = parameter(int)
    maxPhyFrameSize = parameter(int)
    phyFrameOverhead = parameter(int)


@model
class Mac(CastaliaModule):
    """
    int macMaxPacketSize;   // in bytes
    int macBufferSize;      // in number of messages
    int macPacketOverhead;
    """
    macMaxPacketSize = parameter(int)
    macBufferSize = parameter(int)
    macPacketOverhead = parameter(int)



@model
class Omnetpp:
    # Simulation time in sec
    sim_time_limit = attr(float)

    # Simulation time resolution exponent, The default is -9 (nanosec)
    simtime_scale = attr(int, default=-9)

    # CPU time limit, simulation stops when reached. The default is no limit.
    cpu_time_limit = attr(int, default=None)

    # The path to Castalia
    castalia_path = attr(str)


@model
class CastaliaModel:
    omnetpp = attr(type=Omnetpp, nullable=False)
    network = attr(type=CastaliaModule, nullable=False)


MODEL = [
    CastaliaModel, Omnetpp,
    CastaliaModule, 
    Network, WirelessChannel,    
    Node, ResourceManager, SensorManager,
    Application, Communication, Radio, Mac    
]