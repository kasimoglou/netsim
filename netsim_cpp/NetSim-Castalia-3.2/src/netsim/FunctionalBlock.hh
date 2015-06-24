#ifndef _GENERIC_OS_H_
#define _GENERIC_OS_H_

#include <typeinfo>
#include <string>
#include <boost/format.hpp>

#include "CastaliaModule.h"
#include "GenericOS.hh"
#include "ApplicationPacket_m.h"

using namespace std;

template <typename P>
inline string app_packet_name() {
	using boost::format;
	return (format("Packet<%1%>") % typeid(P).name()).str();
}


/*
	This class defines a templetized form of Application message.
 */
template <typename Payload>
class Packet : public ApplicationPacket
{
public:
	typedef Payload payload_type;
private:
	payload_type payload;
public:
	inline Packet() 
		:	ApplicationPacket(app_packet_name<Payload>().c_str(), 
						APPLICATION_PACKET), 
			payload() { }
	inline Packet(const Payload& p) 
		:	ApplicationPacket(app_packet_name<Payload>().c_str(), APPLICATION_PACKET), 
			payload(p) { }
	inline const Payload& getPayload() const { return payload; }
	inline void setPayload(const Payload& p) { payload = p; }

	inline Packet<Payload>* dup() const {  return new Packet<Payload>(*this); }
};




/*
	Base class for a functional block. This class
	attaches to its OS sibling at startup.

	It implements 
 */
class FunctionalBlock : public cSimpleModule {
private:

	GenericOS* _OpSys;

public:

	FunctionalBlock();


	void initialize();

	// Synchronous API 
	template <typename Payload>
	inline void send_packet(const Payload& p, const char* dst) {
		Packet<Payload>* pkt = new Packet<Payload>(p);
		pkt->setByteLength(sizeof(Payload));
		pkt->setSequenceNumber( _OpSys->packetSequenceNumber ++ );
		_OpSys->sendToNetwork(pkt, dst);
	}

	// Async API
	cPacket* receive();
	double read_sensor(int i);

};

#endif

