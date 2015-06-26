
#ifndef _GENERICOS_H_
#define _GENERICOS_H_

#include "VirtualApplication.h"

using namespace std;


class GenericOS : public VirtualApplication {

 public:
	// parameters and variables
	int priority;
	int packetHeaderOverhead;
	int constantDataPayload;
	int packetSequenceNumber;

	void startup();
	void finishSpecific();

	void fromNetworkLayer(ApplicationPacket *, const char *, double, double);
	void timerFiredCallback(int);

	void initialize();

	inline void sendToNetwork(cPacket* p, const char* dest) {
		Enter_Method_Silent();
		take(p);
		toNetworkLayer(p, dest);
	}

};

#endif

