/*
 * @author Ugo Colesanti
 * @author Silvia Santini
 * @version 1.0 (January 27, 2011)
 *
 * Acknowledgment: This code is based upon the implementation of CTP for TinyOS written by
 * Omprakash Gnawali, Philip Levis, Kyle Jamieson, and Rodrigo Fonseca.
 */

/*
 * Copyright (c) 2011 Sapienza University of Rome.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * - Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 * - Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the
 *   distribution.
 * - Neither the name of the Sapienza University of Rome nor the names of
 *   its contributors may be used to endorse or promote products derived
 *   from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL SAPIENZA
 * UNIVERSITY OF ROME OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/*
 * Copyright (c) 2011 ETH Zurich.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * - Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 * - Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the
 *   distribution.
 * - Neither the name of ETH Zurich nor the names of
 *   its contributors may be used to endorse or promote products derived
 *   from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL ETH
 * ZURICH OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef _CTPROUTINGENGINE_H_
#define _CTPROUTINGENGINE_H_

#include "Ctp.h"

using namespace std;


/////////////////////////// TreeRouting.h ////////////////////////////
//////////////////////////////////////////////////////////////////////

enum {
	AM_TREE_ROUTING_CONTROL = 0xCE,
	BEACON_INTERVAL = 8192,
	INVALID_ADDR  = 0xffff,
	ETX_THRESHOLD = 50,      // link quality=20% -> ETX=5 -> Metric=50
	PARENT_SWITCH_THRESHOLD = 15,
	MAX_METRIC = 0xFFFF,
};


typedef struct {
	am_addr_t parent;
	uint16_t etx;
	bool haveHeard;
	bool congested;
} route_info_t;

typedef struct {
	am_addr_t neighbor;
	route_info_t info;
} routing_table_entry;

inline void routeInfoInit(route_info_t *ri) {
	ri->parent = INVALID_ADDR;
	ri->etx = 0;
	ri->haveHeard = 0;
	ri->congested = false ;
}

//////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////


////////////////////////// Custom values /////////////////////////////
//////////////////////////////////////////////////////////////////////

enum{
	BEACON_TIMER = 1,
	ROUTE_TIMER = 2,
	POST_UPDATEROUTETASK = 3,
	POST_SENDBEACONTASK = 4,
};

class beaconRx : public cObject,noncopyable{
public:
	int id ;
	int from;
};

//////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////

class CtpRoutingEngine ;
class LinkEstimator ;
class CtpRoutingEngine: public CastaliaModule , public TimerService{
 protected:

	/////////////////////// CtpRoutingEngineP.nc //////////////////////////
	///////////////////////////////////////////////////////////////////////

	bool ECNOff ;
	bool radioOn ;
	bool running ;
	bool sending ;
	bool justEvicted ;

	route_info_t routeInfo ;
	bool state_is_root;
	am_addr_t my_ll_addr;

	cPacket beaconMsgBuffer ;
	CtpBeacon* beaconMsg ; // we don't need a pointer to the header, we use methods of cPacket instead.

	/* routing table -- routing info about neighbors */
	routing_table_entry* routingTable ;
	uint8_t routingTableActive;

	/* statistics */
	uint32_t parentChanges;
	/* end statistics */

	uint32_t routeUpdateTimerCount;

	uint32_t currentInterval ;
	uint32_t t;
	bool tHasPassed;

	///////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////

	/////////////////////// Custom Variables //////////////////////////////
	///////////////////////////////////////////////////////////////////////

	// Pointers to other modules.
	CtpForwardingEngine *cfe ;
	LinkEstimator *le ;
	ResourceManager* resMgrModule;

	// Beacon Frame size.
	int ctpReHeaderSize ;

	// Node Id.
	int self;

	// Sets a node as root from omnetpp.ini
	bool isRoot ;

	// Arguments of generic module CtpRoutingEngineP
	uint32_t minInterval ;
	uint32_t maxInterval ;
	uint8_t routingTableSize ;

	///////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////


	///////////////// Castalia Functions /////////////////////////////
	//////////////////////////////////////////////////////////////////

	virtual void initialize();
	virtual void handleMessage(cMessage* msg) ;
	void timerFiredCallback(int timer) ;
	virtual ~CtpRoutingEngine() ;

	///////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////

	/////////////////// CtpRoutingEngine functions ////////////////////
	///////////////////////////////////////////////////////////////////

	void chooseAdvertiseTime();
	void resetInterval();
	void decayInterval();
	void remainingInterval() ;

	bool passLinkEtxThreshold(uint16_t etx) ;
	uint16_t evaluateEtx(uint16_t quality) ;

	void updateRouteTask() ;
	void sendBeaconTask() ;

	void event_RouteTimer_fired() ;
	void event_BeaconTimer_fired() ;

	CtpBeacon* getHeader(cPacket* msg) ;

	void routingTableInit() ;
	uint8_t routingTableFind(am_addr_t) ;
	error_t routingTableUpdateEntry(am_addr_t, am_addr_t, uint16_t);
	error_t routingTableEvict(am_addr_t);

	// CtpRoutingPacket Interface -----------------------------------------------
	bool command_CtpRoutingPacket_getOption(cPacket* msg, ctp_options_t opt);
	void command_CtpRoutingPacket_setOption(cPacket* msg, ctp_options_t opt);
	void command_CtpRoutingPacket_clearOption(cPacket* msg, ctp_options_t opt);
	void command_CtpRoutingPacket_clearOptions(cPacket* msg);
	am_addr_t command_CtpRoutingPacket_getParent(cPacket* msg);
	void command_CtpRoutingPacket_setParent(cPacket* msg, am_addr_t addr);
	uint16_t command_CtpRoutingPacket_getEtx(cPacket* msg);
	void command_CtpRoutingPacket_setEtx(cPacket* msg, uint8_t etx);
	// --------------------------------------------------------------------------

	///////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////


	/////////////////// Custom functions //////////////////////////////
	///////////////////////////////////////////////////////////////////

	// generates an event in the module where they should signal it.
	void signal_Routing_routeFound() ;
	void signal_Routing_noRoute() ;

	// AMPacket Interface (just what we need) ------------------------
	am_addr_t command_AMPacket_source(cMessage* msg);
	am_addr_t command_AMPacket_address();
	// ---------------------------------------------------------------

	// functions that simulate the post command of TinyOs
	void post_sendBeaconTask() ;
	void post_updateRouteTask() ;

	///////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////


 public:

	/////////////////// CtpRoutingEngine functions ////////////////////
	///////////////////////////////////////////////////////////////////

	error_t command_StdControl_start();
	error_t command_StdControl_stop() ;
	void event_RadioControl_startDone(error_t error) ;
	void event_RadioControl_stopDone(error_t error) ;

	void event_BeaconSend_sendDone(cMessage* msg, error_t error) ;

	void event_BeaconReceive_receive(cPacket* msg);

	void event_LinkEstimator_evicted(am_addr_t neighbor) ;

	// UnicastNameFreeRouting Interface ------------------------------
	bool command_Routing_hasRoute() ;
	am_addr_t command_Routing_nextHop() ;
	// ---------------------------------------------------------------

	// CtpInfo Interface (Part 1) -------------------------------------------
	error_t command_CtpInfo_getParent(am_addr_t*) ;
	uint8_t command_CtpInfo_getEtx(uint16_t* etx) ;
	void command_CtpInfo_recomputeRoutes() ;
	void command_CtpInfo_triggerRouteUpdate() ;
	void command_CtpInfo_triggerImmediateRouteUpdate() ;
	void command_CtpInfo_setNeighborCongested(uint16_t n,bool congested) ;
	bool command_CtpInfo_isNeighborCongested(uint16_t addr) ;
	// ----------------------------------------------------------------------

	// RootControl Interface ------------------------------------------------
	bool command_RootControl_isRoot();
	error_t command_RootControl_setRoot() ;
	error_t command_RootControl_unsetRoot() ;
	// ----------------------------------------------------------------------

	bool event_CompareBit_shouldInsert(cPacket *msg, bool white_bit) ;

	// CtpInfo Interface (Part 2) -------------------------------------------
	uint8_t command_CtpInfo_numNeighbors() ;
	uint16_t command_CtpInfo_getNeighborLinkQuality(uint8_t) ;
	uint16_t command_CtpInfo_getNeighborRouteQuality(uint8_t) ;
	am_addr_t command_CtpInfo_getNeighborAddr(uint8_t) ;
	// ----------------------------------------------------------------------

	///////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////

};
#endif
