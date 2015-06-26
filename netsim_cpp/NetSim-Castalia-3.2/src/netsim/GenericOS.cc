
#include "GenericOS.h"

Define_Module(GenericOS);

/*
	N.B. this code is taken from Castalia's VirtualApplication::initialize()
	function. We needed to change this code, since the 

 */
void GenericOS::initialize()
{
	/* Get a valid references to the objects of the Resources Manager module
	 * the Mobility module and the Radio module, so that we can make direct
	 * calls to their public methods
	 */

	 /*
	 	Changed: go up the hierarchy until you reach the node!
	  */
	cModuleType* nodeType = cModuleType::get("node.Node");
	cModule *parent = getParentModule();
	while( parent->getModuleType() != nodeType ) {
		EV << "Parent name: " << parent->getName() << endl;
		parent = parent->getParentModule();
	}
	EV << "Parent found: " << parent->getName() << endl;


	resMgrModule = check_and_cast <ResourceManager*>(parent->getSubmodule("ResourceManager"));
	mobilityModule = check_and_cast <VirtualMobilityManager*>(parent->getSubmodule("MobilityManager"));
	radioModule = check_and_cast <Radio*>(parent->getSubmodule("Communication")->getSubmodule("Radio"));
	// check that all the pointers are valid
	if (!resMgrModule || !mobilityModule || !radioModule)
		opp_error("\n Virtual App init: Error in geting a valid reference module(s).");

	self = parent->getIndex();
	// create the routing level address using self
	stringstream out; out << self; selfAddress = out.str();

	cpuClockDrift = resMgrModule->getCPUClockDrift();
	setTimerDrift(cpuClockDrift);
	disabled = true;

	applicationID = par("applicationID").stringValue(); // make sure par() returns a string
	priority = par("priority");
	packetHeaderOverhead = par("packetHeaderOverhead");
	constantDataPayload = par("constantDataPayload");
	isSink = hasPar("isSink") ? par("isSink") : false;

	double startup_delay = parent->par("startupOffset");
	// Randomize the delay if the startupRandomization is non-zero
	startup_delay += genk_dblrand(0) * (double)parent->par("startupRandomization");

	/* Send the STARTUP message to 1)Sensor_Manager, 2)Commmunication module,
	 * 3) Resource Manager, and $)APP (self message) so that the node starts
	 * operation. Note that we send the message to the Resource Mgr through
	 * the unconnected gate "powerConsumption" using sendDirect()
	 */
	sendDelayed(new cMessage("Sensor Dev Mgr [STARTUP]", NODE_STARTUP),
		    simTime() +  startup_delay, "toSensorDeviceManager");
	sendDelayed(new cMessage("Communication [STARTUP]", NODE_STARTUP),
		    simTime() +  startup_delay, "toCommunicationModule");
	sendDirect(new cMessage("Resource Mgr [STARTUP]", NODE_STARTUP),
		    startup_delay, 0, resMgrModule, "powerConsumption");
	scheduleAt(simTime() + startup_delay, new cMessage("App [STARTUP]", NODE_STARTUP));

	/* Latency measurement is optional. An application can define the
	 * following two parameters. If they are not defined then the
	 * declareHistogram and collectHistogram statement are not called.
	 */
	latencyMax = hasPar("latencyHistogramMax") ? par("latencyHistogramMax") : 0;
	latencyBuckets = hasPar("latencyHistogramBuckets") ? par("latencyHistogramBuckets") : 0;
	if (latencyMax > 0 && latencyBuckets > 0)
		declareHistogram("Application level latency, in ms", 0, latencyMax, latencyBuckets);
}



void GenericOS::startup()
{
	EV << "Startup node " << getFullPath() << endl;
	packetSequenceNumber = 0;
}

void GenericOS::fromNetworkLayer(ApplicationPacket * rcvPacket, const char *source, double rssi, double lqi)
{
	
}

void GenericOS::timerFiredCallback(int timerIndex)
{
	// switch (timerIndex) {
	// 	case SEND_PACKET:{
	// 		break;
	// 	}
	// }
}

void GenericOS::finishSpecific()
{
	VirtualApplication::finishSpecific();
	// declareOutput("Packets received");
	// for (int i = 0; i < (int)neighborTable.size(); i++) {
	// 	collectOutput("Packets received", neighborTable[i].id,
	// 		      "Success", neighborTable[i].receivedPackets);
	// }
}

