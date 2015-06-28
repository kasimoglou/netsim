
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


int GenericOS::addPeriodicTask(PeriodicTask* task)
{
	int timer_id = periodicTasks.size();
	periodicTasks.push_back(task);
	return timer_id;
}


void GenericOS::addSensorBuffer(SensorBuffer* sensorBuffer)
{
	sensorBuffers[sensorBuffer->sensorIndex] = sensorBuffer;
}



void GenericOS::startup()
{
	EV << "Startup node " << getFullPath() << endl;
	packetSequenceNumber = 0;
}

void GenericOS::fromNetworkLayer(ApplicationPacket * rcvPacket, const char *source, double rssi, double lqi)
{
	typedef map<int, MessageHandler>::iterator Iter;

	int messageClass = getMessageClass(rcvPacket);
	Iter found = handlers.find(messageClass);
	if(found != handlers.end()) {
		(*found).second(rcvPacket, source, rssi, lqi);
	}
}

void GenericOS::timerFiredCallback(int timerIndex)
{
	if(timerIndex<0 || timerIndex >= periodicTasks.size())
		opp_error("timerFiredCallback() "
			"called for task out of range.");
	periodicTasks[timerIndex]->fired();
}

void GenericOS::finishSpecific()
{
	VirtualApplication::finishSpecific();
}


void GenericOS::send_message(ApplicationPacket* packet, const char* dest)
{
	toNetworkLayer(packet, dest);
}


void GenericOS::fireTimerAfter(int timer_id, simtime_t duration)
{
	setTimer(timer_id, simTime()+duration);
}


//
//  Periodic task
//

PeriodicTask::PeriodicTask(GenericOS* __OS)
	: AppModule(__OS), period() 
{
	timer_id = OS->addPeriodicTask(this);
}


void DataBuffer::record(double m)
{
	measurement.push_back(m);
	m_time.push_back(simTime());
}


//
//  Sensor buffer
//



void SensorBuffer::request()
{
	OS->requestSensorReading(sensorIndex);
}


SensorReadTask::SensorReadTask(GenericOS* __OS)
   : AppModule(__OS), PeriodicTask(__OS)
{
}

void SensorReadTask::task()
{
	sensorBuffer->request();
}



