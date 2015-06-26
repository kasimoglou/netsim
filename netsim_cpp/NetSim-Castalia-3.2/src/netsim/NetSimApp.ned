
//
//	This is the Castalia composite module that encapsulates the application
//  in each node.
//


package netsim;

// The sensor node module. Connects to the wireless channel in order to communicate 
// with other nodes. Connects to psysical processes so it can sample them.

module NetSimApp like node.application.iApplication {
 
 parameters:
 	string applicationID = default ("NetSimApp");
	bool collectTraceInfo = default (false);

	int packetHeaderOverhead = default (8);
	int priority = default (1);
	int constantDataPayload = default (8);

	string OsName = default("GenericOS");
 	int numBlocks = default(0);

 gates:
 	output toCommunicationModule;
	output toSensorDeviceManager;
	input fromCommunicationModule;
	input fromSensorDeviceManager;
	input fromResourceManager;

submodules:
 	Os : <OsName> like node.application.iApplication;
 	block[numBlocks] : <> like FunctionalBlock;

 connections:
 	fromCommunicationModule --> Os.fromCommunicationModule;
 	fromSensorDeviceManager --> Os.fromSensorDeviceManager;
 	fromResourceManager -->  Os.fromResourceManager;
 	Os.toCommunicationModule --> toCommunicationModule;
 	Os.toSensorDeviceManager --> toSensorDeviceManager;
}

