/*
 * @author Ugo Colesanti
 * @author Silvia Santini
 * @version 1.01 (January 3, 2012)
 *
 * Acknowledgment: This code is based upon the implementation of CTP for TinyOS written by
 * Omprakash Gnawali, Philip Levis, Kyle Jamieson, and Rodrigo Fonseca.
 */

/*
 * Copyright (c) 2012 Sapienza University of Rome.
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
 * Copyright (c) 2012 ETH Zurich.
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

/*
 * Copyright (c) 2006 Stanford University.
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
 * - Neither the name of the Stanford University nor the names of
 *   its contributors may be used to endorse or promote products derived
 *   from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL STANFORD
 * UNIVERSITY OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef _CTPFORWARINGENGINE_H_
#define _CTPFORWARINGENGINE_H_

#include "Ctp.h"
#include "Pool.h"

/////////////////////// CtpForwardingEngine.h ////////////////////////
//////////////////////////////////////////////////////////////////////

enum {
	FORWARD_PACKET_TIME = 4,
};

enum {
	SENDDONE_FAIL_OFFSET      =                       512,
	SENDDONE_NOACK_OFFSET     = FORWARD_PACKET_TIME  << 2,
	SENDDONE_OK_OFFSET        = FORWARD_PACKET_TIME  << 2,
	LOOPY_OFFSET              = FORWARD_PACKET_TIME  << 4,
	SENDDONE_FAIL_WINDOW      = SENDDONE_FAIL_OFFSET  - 1,
	LOOPY_WINDOW              = LOOPY_OFFSET          - 1,
	SENDDONE_NOACK_WINDOW     = SENDDONE_NOACK_OFFSET - 1,
	SENDDONE_OK_WINDOW        = SENDDONE_OK_OFFSET    - 1,
	CONGESTED_WAIT_OFFSET     = FORWARD_PACKET_TIME  << 2,
	CONGESTED_WAIT_WINDOW     = CONGESTED_WAIT_OFFSET - 1,
};

enum {
	MAX_RETRIES = 30,
};

// network_header_t removed: declared but never used.

typedef struct {
	cPacket* msg ;
	uint8_t client;
	uint8_t retries;
} fe_queue_entry_t;

//////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////



////////////////////////// Utility values ////////////////////////////
//////////////////////////////////////////////////////////////////////

enum{
	CLIENT_COUNT = 1,
	DEFAULT_CLIENT_ID = 0,
};

enum{
	RETXTIMER = 1,
	CONGESTION_TIMER = 2 ,
	POST_SENDTASK = 3,
};

//////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////

using namespace std;
class DualBuffer ;
class CtpRoutingEngine ;
class LinkEstimator ;
class CtpForwardingEngine: public CastaliaModule , public TimerService{
protected:

	///////////////////// CtpForwardingEngineP.nc /////////////////////////
	///////////////////////////////////////////////////////////////////////

	bool clientCongested;
	bool parentCongested;
	uint8_t congestionThreshold;
	bool running;
	bool radioOn;
	bool ackPending;
	bool sending;
	am_addr_t lastParent;
	uint8_t seqno;

	//////////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////////

	/////////////////////////// Custom Variables ////////////////////////
	/////////////////////////////////////////////////////////////////////

	// Pointers to other modules.
	DualBuffer *db ;
	CtpRoutingEngine *cre ;
	LinkEstimator *le ;
	ResourceManager* resMgrModule;

	// Data Frame Overhead.
	int ctpFeHeaderSize ;

	// Node id
	int self;
	string selfAddress ;

	// Single client support.
	uint8_t global_client ;
	fe_queue_entry_t clientEntries;
	fe_queue_entry_t* clientPtrs ;


	// Needed for SendQueue Interface.
	queue<fe_queue_entry_t*> sendqueue ;
	uint8_t queueMaxSize ;

	// Required by our implementation of timers.
	bool congestionTimerIsRunning ;
	bool reTxTimerIsRunning ;

	// Needed for SentCache Interface.
	vector<cPacket*> sentCache ;
	int sentCacheSize ;

	// Needed for Pool Interfaces.
	Pool<cPacket>* messagePool ;
	Pool<fe_queue_entry_t>* qEntryPool ;

	///////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////

	///////////// Castalia Functions /////////////////////////////////
	//////////////////////////////////////////////////////////////////

	virtual void initialize();
	virtual void handleMessage(cMessage * msg);
	void timerFiredCallback(int timer) ;
	virtual ~CtpForwardingEngine() ;

	///////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////

	///////////////// CtpForwardingEngine functions ///////////////////
	///////////////////////////////////////////////////////////////////

	CtpData* getHeader(cPacket* pkt);
	void sendTask() ;
	void forward(cPacket* pkt);
 	void event_SubReceive_receive(cPacket*) ;
 	void event_SubSnoop_receive(cPacket*) ;
 	void event_RetxmitTimer_fired() ;
	void event_CongestionTimer_fired() ;

	// CtpPacket Interface ----------------------------------------------
	uint8_t command_CtpPacket_getType(cPacket* pkt) ;
	uint16_t command_CtpPacket_getOrigin(cPacket* pkt) ;
	uint16_t command_CtpPacket_getEtx(cPacket* pkt) ;
	uint8_t command_CtpPacket_getSequenceNumber(cPacket* pkt) ;
	uint8_t command_CtpPacket_getThl(cPacket* pkt) ;
	bool command_CtpPacket_option(cPacket* pkt, uint8_t opt) ;
	void command_CtpPacket_setOption(cPacket* pkt, uint8_t opt) ;
	void command_CtpPacket_clearOption(cPacket* pkt, uint8_t opt) ;
	void command_CtpPacket_setEtx(cPacket* pkt,uint16_t e);
	bool command_CtpPacket_matchInstance(cPacket* pkt1, cPacket* pkt2);
	// ------------------------------------------------------------------

	void startRetxmitTimer(uint16_t mask, uint16_t offset) ;
	void startCongestionTimer(uint16_t mask, uint16_t offset);

	///////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////


	///////////////////////// Custom Functions ///////////////////////////
	//////////////////////////////////////////////////////////////////////

	void post_sendTask() ;

	// AMPacket Interface (just what we need) -------------------------------
	uint16_t command_AMPacket_address() ;
	uint16_t command_AMPacket_source(cMessage* msg) ;
	uint16_t command_AMPacket_destination(cMessage* msg) ;
	// ----------------------------------------------------------------------

	void encapsulatePacket(CtpData * pkt, cPacket * appPkt) ;

	// SendQueue Interface -------------------------------------------------
	uint8_t command_SendQueue_maxSize() ;
	bool command_SendQueue_empty() ;
	error_t command_SendQueue_enqueue(fe_queue_entry_t*) ;
	uint8_t command_SendQueue_size() ;
	fe_queue_entry_t* command_SendQueue_dequeue() ;
	fe_queue_entry_t* command_SendQueue_element(uint8_t idx) ;
	fe_queue_entry_t* command_SendQueue_head() ;
	// --------------------------------------------------------------------

	// SentCache Interface ------------------------------------------------
	void command_SentCache_insert(cPacket* pkt);
	bool command_SentCache_lookup(cPacket* pkt);
	void command_SentCache_flush();
	// --------------------------------------------------------------------

	bool command_PacketAcknowledgements_wasAcked(cMessage* msg);

	void signal_Send_sendDone(error_t err) ;

	void toApplicationLayer(cMessage* pkt) ;

	/////////////////////////////////////////////////////////////////////
	/////////////////////////////////////////////////////////////////////

public:
	///////////////// CtpForwardingEngine functions ///////////////////
	///////////////////////////////////////////////////////////////////

	error_t command_StdControl_start() ;
	error_t command_StdControl_stop() ;
	void event_RadioControl_startDone(error_t err) ;
 	void event_UnicastNameFreeRouting_routeFound();
 	void event_UnicastNameFreeRouting_noRoute();
 	void event_RadioControl_stopDone(uint8_t err) ;
 	error_t command_Send_send(cPacket* msg, uint8_t len);
 	error_t command_Send_cancel();
 	void event_SubSend_sendDone(cMessage*, error_t err) ;

 	// CtpCongestion Interface --------------------------
 	bool command_CtpCongestion_isCongested() ;
 	void command_CtpCongestion_setClientCongested(bool) ;
 	// --------------------------------------------------

 	void event_send_sendDone(uint8_t err) ;
 	void event_LinkEstimator_evicted(am_addr_t neighbor) ;

 	uint8_t getSeqNo() ;

 	///////////////////////////////////////////////////////////////////
 	///////////////////////////////////////////////////////////////////


};
#endif
