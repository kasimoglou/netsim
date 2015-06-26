
//--------------------------------------------------------------------
//
//	The main module for application execution support. This
//  module connects to all other modules of the node model.  
//
//--------------------------------------------------------------------


package netsim;

// extends iApplication, as does the composite.

simple GenericOS like node.application.iApplication {
 parameters:
 	string applicationID = default ("GenericOs");
	bool collectTraceInfo = default (false);
	int packetHeaderOverhead = default (8);
	int priority = default (1);
	int constantDataPayload = default (8);

	double latencyHistogramMax = default (400);
	int latencyHistogramBuckets = default (100);

 gates:
 	output toCommunicationModule;
	output toSensorDeviceManager;
	input fromCommunicationModule;
	input fromSensorDeviceManager;
	input fromResourceManager;
}

