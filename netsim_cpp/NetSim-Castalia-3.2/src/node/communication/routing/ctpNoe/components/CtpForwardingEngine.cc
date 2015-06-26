/*
 * @author Ugo Colesanti
 * @author Silvia Santini
 * Acknowledgment: This code is based upon the implementation of CTP for TinyOS written by
 * Omprakash Gnawali, Philip Levis, Kyle Jamieson, and Rodrigo Fonseca.
 *
 * @version 1.02 (January 3, 2012)
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
 
#include "CtpForwardingEngine.h"
#include "CtpRoutingEngine.h"
#include "LinkEstimator.h"
#include "DualBuffer.h"
Define_Module(CtpForwardingEngine);

void CtpForwardingEngine::initialize(){

	//////////////////////// Castalia Implementation ////////////////////
	/////////////////////////////////////////////////////////////////////

	//Pointers to other modules for direct function calls.
	db = check_and_cast<DualBuffer*>(getParentModule()->getSubmodule("DualBuffer")) ;
	cre = check_and_cast<CtpRoutingEngine*>(getParentModule()->getSubmodule("CtpRoutingEngine")) ;
	le = check_and_cast<LinkEstimator*>(getParentModule()->getSubmodule("LinkEstimator")) ;

	//Id of the node (like TOS_NODE_ID)
	self = getParentModule()->getParentModule()->getParentModule()->getIndex();

	// Since we don't know whether a timer is running, we put these bool values
	// to true when the timer is launched and to false when it fires.
	congestionTimerIsRunning = false ;
	reTxTimerIsRunning = false ;

	// The default values are set in CtpForwardingEngine.ned
	// but they can be overwritten in the omnetpp.ini
	sentCacheSize = par("sentCacheSize") ; // replaces "Cache as SentCache" in the CtpForwardingEngine (default 4 messages)
	ctpFeHeaderSize = par("ctpFeHeaderSize") ; // Data frame overhead (default 8 bytes)



	// this variable replaces the client parameter in the CtpForwardingEngine.
	global_client = DEFAULT_CLIENT_ID ;

	// The send queue defined as "Queue<fe_queue_entry_t*> as SendQueue" in the CtpForwardingEngine
	// is replaced by a set of functions at the end of this class. This parameter sets the size of the
	// queue which by default is 13 (CLIENT_COUNT + FORWARD_COUNT) but can be overwritten in the omnetpp.ini
	queueMaxSize = par("sendQueueMaxSize") ;

	// The Pool template emulates the Pool component n TinyOs. It is defined in Pool.h
	messagePool = new Pool<cPacket>(queueMaxSize-1) ; // replaces "Pool<message_t> as MessagePool"
	qEntryPool = new Pool<fe_queue_entry_t>(queueMaxSize-1) ; // replaces "Pool<fe_queue_entry_t> as QEntryPool"

	// Clock drift simulation (it is present at each layer)
	if (getParentModule()->getParentModule()->getParentModule()->findSubmodule("ResourceManager") != -1) {
		resMgrModule = check_and_cast <ResourceManager*>(getParentModule()->getParentModule()->getParentModule()->getSubmodule("ResourceManager"));
	} else {
		opp_error("\n[Mac]:\n Error in geting a valid reference to ResourceManager for direct method calls.");
	}
	setTimerDrift(resMgrModule->getCPUClockDrift());

	/////////////////////////////////////////////////////////////////////
	/////////////////////////////////////////////////////////////////////


	///////////////////// CtpForwardingEngine (default) /////////////////
	/////////////////////////////////////////////////////////////////////

	clientCongested = false;
	parentCongested = false;
	running = false;
	radioOn = true; // TO IMPLEMENT ------------- radioOn must be off then turned on when radio control event is triggered
	ackPending = false;
	sending = false;

	//////////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////////


	/////////////////////////// Init.init() /////////////////////////////
	/////////////////////////////////////////////////////////////////////

	clientPtrs = &clientEntries ; // we support one client only -> we don't use an array
	congestionThreshold = command_SendQueue_maxSize() >> 1 ;
	lastParent = command_AMPacket_address() ;
	seqno = 0;

	//	Notes: we don't use loopbackMsgPtr thus:
	//	loopbackMsgPtr = &loopbackMsg;
	//	is not useful in our implementation

	//////////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////////

	/////////////////////////// Init.init() /////////////////////////////
	/////////////////////////////////////////////////////////////////////

	declareOutput("Ctp Data") ;

	/////////////////////////////////////////////////////////////////////
	/////////////////////////////////////////////////////////////////////
};

void CtpForwardingEngine::handleMessage(cMessage * msg){
	int msgKind = msg->getKind();
	switch (msgKind) {
		case APPLICATION_PACKET:{
			trace()<<"App from CtpNoe ..." ;
			cPacket *pkt = check_and_cast<cPacket*>(msg) ;
			command_Send_send(pkt,(uint8_t)pkt->getByteLength()) ;
			return; // because the msg handling passes to another module
		}
		case MAC_CONTROL_MESSAGE:{
			break;
		}
		case NETWORK_CONTROL_COMMAND:{
			break;
		}
		case NETWORK_LAYER_PACKET:{
			RoutingPacket* rt = check_and_cast<RoutingPacket*>(msg) ;
			if(rt->getNetMacInfoExchange().nextHop == self){
				CtpData *netPkt = check_and_cast <CtpData*>(msg);
				//			send(decapsulatePacket(netPkt),"toCtp") ;
				event_SubReceive_receive(netPkt) ;
			}
			else{
				CtpData *netPkt = check_and_cast <CtpData*>(msg);
				event_SubSnoop_receive(netPkt) ;
			}


			return ;
		}
		case TIMER_SERVICE:{
			handleTimerMessage(msg);
			break;
		}
	}

	delete msg ;
};


void CtpForwardingEngine::timerFiredCallback(int timer)
{
	trace() << "CtpFE - TimerFiredCallback, value: "<<timer;
	switch (timer) {

		case RETXTIMER:{
			event_RetxmitTimer_fired() ;
			reTxTimerIsRunning = false ;
			break;
		}
		case CONGESTION_TIMER:{
			event_CongestionTimer_fired() ;
			congestionTimerIsRunning = false ;
			break;
		}
		case POST_SENDTASK:{
			sendTask() ;
			break ;
		}

		default:{
			opp_error("Unexpected message!");
		}
	}
}

CtpForwardingEngine::~CtpForwardingEngine(){

	// clear the sendQueue
	while(!command_SendQueue_empty()){
		fe_queue_entry_t* qe = command_SendQueue_dequeue() ;
		collectOutput("Ctp Data","Tx Dropped - In SendQueue at finish") ;
		delete qe->msg ;
	}

	// clear the sentCache
	for (unsigned int i=0; i<sentCache.size(); i++){
		delete sentCache[i] ;
	}
	sentCache.clear() ;

	// free pools
	delete qEntryPool ;
	delete messagePool ;

	qEntryPool = NULL ;
	messagePool = NULL ;

}


error_t CtpForwardingEngine::command_StdControl_start(){
	Enter_Method("command_StdControl_start") ;
	running = true ;
	return SUCCESS ;
}

error_t CtpForwardingEngine::command_StdControl_stop(){
	Enter_Method("command_StdControl_stop") ;
	running = false ;
	return SUCCESS ;
}

void CtpForwardingEngine::event_RadioControl_startDone(error_t err){
	Enter_Method("event_RadioControl_startDone") ;
	if(err == SUCCESS) {
	  radioOn = true;
	  if (! command_SendQueue_empty()) {
		  post_sendTask();
	  }
	}
}

void CtpForwardingEngine::event_UnicastNameFreeRouting_routeFound(){
	Enter_Method("event_UnicastNameFreeRouting_routeFound") ;
	trace()<<"Route found!" ;
	post_sendTask() ;
}

void CtpForwardingEngine::event_UnicastNameFreeRouting_noRoute(){
	Enter_Method("event_UnicastNameFreeRouting_noRoute") ;
	trace()<<"No Route!" ;
	// nope
}

void CtpForwardingEngine::event_RadioControl_stopDone(error_t err){
	Enter_Method("event_RadioControl_stopDone") ;
	if (err == SUCCESS) {
		  radioOn = false;
    }
}

/*
 * We don't need a pointer to the header, we can use the methods of cPacket
 * instead, we return a pointer to CtpData and that's it.
 */
CtpData* CtpForwardingEngine::getHeader(cPacket* pkt){
	CtpData* res = check_and_cast<CtpData*>(pkt) ;
	return res ;
}

error_t CtpForwardingEngine::command_Send_send(cPacket* pkt, uint8_t len){
	Enter_Method("command_Send_send") ;
	collectOutput("Ctp Data","Tx from App layer.") ;
	fe_queue_entry_t *qe;
	trace()<<"command_Send_send - Sending packet from client "<<(int)global_client<<" with length: "<<(int)len;
	if (!running) {
		collectOutput("Ctp Data","Tx Dropped - not running") ;
		emit(registerSignal("CfeTxDroppedNotRunning"),self) ;
		delete pkt ;
		return EOFF;
	}
	if(len > TOSH_DATA_LENGTH){
		collectOutput("Ctp Data","Tx Dropped - Too long") ;
		emit(registerSignal("CfeTxDroppedTooLong"),self) ;
		delete pkt ;
		return ESIZE;
	}

	/*
	 * We don't need memory allocation since we initialize a new cPacket.
	 * The header is set in the encapsulatePacket function.
	 */
	CtpData *msg = new CtpData("Ctp Data Packet packet", NETWORK_LAYER_PACKET);
	encapsulatePacket(msg, pkt);

	if (clientPtrs == NULL) {
		trace()<<"Send.send - send failed as client is busy." ;
		collectOutput("Ctp Data","Tx Dropped - busy") ;
		emit(registerSignal("CfeTxDroppedEbusy"),self) ;
		delete msg ;
		return EBUSY;
	}

	qe = clientPtrs;
	qe->msg = msg;
	qe->client = global_client;
	qe->retries = MAX_RETRIES;

	trace()<<"command_Send_send - Queue entry for "<<(int)global_client<<" is "<<(int)command_SendQueue_size()<<" deep" ;
	if (command_SendQueue_enqueue(qe) == SUCCESS) {
		if(radioOn && !reTxTimerIsRunning){
			post_sendTask() ;
		}
		clientPtrs = NULL;
		return SUCCESS;
	}
	else {
		trace()<<"Send.send - Send failed as packet could not be enqueued." ;
		collectOutput("Ctp Data","Tx Dropped - sendQueue full") ;
		delete msg ;
		return FAIL;
	}
}

error_t CtpForwardingEngine::command_Send_cancel() {
	Enter_Method("command_Send_cancel") ;
    return FAIL;
}

//command uint8_t Send.maxPayloadLength[uint8_t client]() { not useful
//uint8_t CtpForwardingEngine::command_Send_maxPayloadLength() {
//	Enter_Method("command_Send_maxPayloadLength") ;
//
//}

//command void* Send.getPayload[uint8_t client](message_t* msg, uint8_t len) { not useful
//	return call Packet.getPayload(msg, len);
//}

void CtpForwardingEngine::sendTask(){
	trace()<<"sendTask - Trying to send a packet. Queue size is: " << (int) command_SendQueue_size() ;
	if (sending) { // NOT CHECKED
		trace()<<"sendTask - Busy, don't send.";
		return;
	}
	else if (command_SendQueue_empty()) { // CHECK -> OK: when queue empty do nothing.
		trace()<<"sendTask - Queue empty, don't send." ;
		return;
	}
	else if (! cre->command_RootControl_isRoot()  &&
			! cre->command_Routing_hasRoute()) { // CHECK -> OK: retx called after 9.76 sec.
		trace()<<"sendTask - No route, don't send, start retry timer." ;
		emit(registerSignal("CfeTxDelayedNoRoute"),self) ;
		setTimer(RETXTIMER,tosMillisToSeconds(10000)) ;

		return;
	}
	else {
		error_t subsendResult ;
		fe_queue_entry_t* qe = command_SendQueue_head();
		am_addr_t dest = cre->command_Routing_nextHop() ;
		uint16_t gradient;

		if (cre->command_CtpInfo_isNeighborCongested(dest)) { // NOT CHECKED
			// Our parent is congested. We should wait.
			// Don't repost the task, CongestionTimer will do the job
			emit(registerSignal("CfeTxDelayedParentCongested"),self) ;
			if (! parentCongested ) {
				parentCongested = true;
			}
			if (! congestionTimerIsRunning) {
				startCongestionTimer(CONGESTED_WAIT_WINDOW, CONGESTED_WAIT_OFFSET);
			}
			trace() << "sendTask - sendTask deferring for congested parent." ;
			return;
		}
		if (parentCongested) {
			parentCongested = false;
		}
		// Once we are here, we have decided to send the packet.
		if(command_SentCache_lookup(qe->msg)){ // NOT CHECKED
			collectOutput("Ctp Data","Tx Dropped - was in sent cache") ;
			emit(registerSignal("CfeDupDroppedInSentCache"),self) ;
			command_SendQueue_dequeue() ;
			if(messagePool->command_Pool_put(qe->msg) != SUCCESS) trace() << "message pool error." ;
			delete qe->msg ; // we need to delete the allocated packet.
			if(qEntryPool->command_Pool_put(qe) != SUCCESS) trace()<<"qentry error.";
			post_sendTask() ;
			return;
		}
		/* If our current parent is not the same as the last parent
         we sent do, then reset the count of unacked packets: don't
         penalize a new parent for the failures of a prior one.*/
		if (dest != lastParent) { // CHECK -> OK: qe retries initialized
			trace() <<"the parent has changed since last time...";
			qe->retries = MAX_RETRIES;
			lastParent = dest;
		}

		trace()<<"Sending queue entry." ;
		if (cre->command_RootControl_isRoot()) { // CHECK -> OK: loppbacked message to app layer.
			collectOutput("Ctp Data","Tx - Loopback Message") ;
			emit(registerSignal("CfeTxOkIsLoopback"),self) ;
			// there is a collectionid (needed for signal receive) that is useless in our implementation: it has been removed.
			// here there is a memcpy for loopbackMsgPtr that we don't need to implement, we use msg->dup() instead later.
			ackPending = false;

			//        dbg("Forwarder", "%s: I'm a root, so loopback and signal receive.\n", __FUNCTION__);
			trace()<<"sendTask - I'm root, so loopback and signal receive.";

			// We send the packet to the application layer -> it replaces the signal Receive.receive.
			cPacket* dupMsg = qe->msg->dup() ;
			toApplicationLayer(dupMsg->decapsulate()) ; // dup because it's a loopback message, it must be deleted in event_SubSend_sendDone
			delete dupMsg ;

			// Following the mapping rules we defined, we signal the sendDone event with a CC2420MacControlMessage.
			CC2420MacControlMessage* cc2420control = new CC2420MacControlMessage() ; // need to emulate a CC2420MacControlMessage
			cc2420control->setMetaDest(command_AMPacket_address()) ;
			cc2420control->setMetaWasAcked(false) ; // not significant since ackpending is false
			event_SubSend_sendDone(cc2420control,SUCCESS) ;
			delete cc2420control ; // we need to delete the self-generated message.
			return;
		}

		// Loop-detection functionality:
		if (cre->command_CtpInfo_getEtx(&gradient) != SUCCESS) { // NOT CHECKED
			// If we have no metric, set our gradient conservatively so
			// that other nodes don't automatically drop our packets.
			gradient = 0;
		}

		command_CtpPacket_setEtx(qe->msg,gradient) ;

		ackPending = true ; // the acknowledgement is automatically requested for Unicast packets in the implemented CC2420Mac

		// Set or clear the congestion bit on *outgoing* packets.
		if(command_CtpCongestion_isCongested()) command_CtpPacket_setOption(qe->msg, CTP_OPT_ECN) ;
		else command_CtpPacket_clearOption(qe->msg, CTP_OPT_ECN) ;

		subsendResult = db->command_Send_send(dest,qe->msg->dup()) ; // the duplicate will be sent via the dual buffer module. we keep a copy here that will be deleted fater the sendDone.
		if (subsendResult == SUCCESS) { // CHECK -> OK
			// Successfully submitted to the data-link layer.
			collectOutput("Ctp Data","Tx - to Dual Buffer") ;
			sending = true;
			trace()<<"sendTask - subsend succeeded." ;
			if (qe->client < CLIENT_COUNT) {
				emit(registerSignal("CfeTxOkClient"),self) ;
				trace()<<"sendTask - client packet.";
			}
			else {
				emit(registerSignal("CfeTxOkForwarded"),self) ;
				trace()<<"sendTask - Forwarded packet." ;
			}
			return;
		}
		else if (subsendResult == EOFF) { // NOT CHECKED
			// The radio has been turned off underneath us. Assume that
			// this is for the best. When the radio is turned back on, we'll
			// handle a startDone event and resume sending.
			radioOn = false;
			emit(registerSignal("CfeTxDroppedRadioOff"),self) ;
			trace()<<"sendTask - Subsend failed from EOFF." ;
		}
		else if (subsendResult == EBUSY) { // CHECKED -> OK
			// This shouldn't happen, as we sit on top of a client and
			// control our own output; it means we're trying to
			// double-send (bug). This means we expect a sendDone, so just
			// wait for that: when the sendDone comes in, // we'll try
			// sending this packet again.
			emit(registerSignal("CfeTxDroppedRadioEbusy"),self) ;
			trace()<<"sendTask - Subsend failed from EBUSY" ;
			// CASTALIA IMPLEMENTATION: this condition might happen when a "route found" is signaled from the RE and a ReTxTimer is running:
			// the first event calls a post sendTask(), if the ReTxTimer fires before the sendDone, the sending flag is set to false and a new sendTask is called.
			// It's rare but it happens during loops, in particular when the current parent may select ourselves as parent (check updateRouteTask in RE)
			// Is it a bug of CTP or of my implementation?

			//opp_error("Subsend failed from EBUSY") ; // put here just to check if it ever happens.
		}
		else if (subsendResult == ESIZE) {
			trace()<<"sendTask - Subsend failed from ESIZE: truncate packet." ;
			post_sendTask();
			opp_error("ESIZE: truncated packet -> it's not possible in castalia...") ;
		}
	}
}

//void sendDoneBug() {
//  // send a debug message to the uart
//  call CollectionDebug.logEvent(NET_C_FE_BAD_SENDDONE);
//}



/*
   * The second phase of a send operation; based on whether the transmission was
   * successful, the ForwardingEngine either stops sending or starts the
   * RetxmitTimer with an interval based on what has occured. If the send was
   * successful or the maximum number of retransmissions has been reached, then
   * the ForwardingEngine dequeues the current packet. If the packet is from a
   * client it signals Send.sendDone(); if it is a forwarded packet it returns
   * the packet and queue entry to their respective pools.
   *
   */

void CtpForwardingEngine::event_SubSend_sendDone(cMessage* msg, error_t error){
	Enter_Method("event_SubSend_sendDone") ;
	fe_queue_entry_t *qe = command_SendQueue_head() ;
	trace()<<"SubSend.sendDone - to: "<<(int)command_AMPacket_destination(msg)<<" and : "<<(int)error ;

	if (qe == NULL /*|| qe->msg != msg*/) { // cannot check the pointer since I dup the message
		opp_error("BUG1\n") ; // stop the simulation -> it should never happen.
	}
	else if (error != SUCCESS) { // NOT CHECKED
		// Immediate retransmission is the worst thing to do.
		trace()<<"SubSend.sendDone - Send failed";
		emit(registerSignal("CfeTxDoneFailed"),self) ;
		startRetxmitTimer(SENDDONE_FAIL_WINDOW, SENDDONE_FAIL_OFFSET);
	}
	else if (ackPending && !command_PacketAcknowledgements_wasAcked(msg)) { // CHECK -> OK: see inner statements
		// AckPending is for case when DL cannot support acks.
		le->command_LinkEstimator_txNoAck(command_AMPacket_destination(msg)) ;
		cre->command_CtpInfo_recomputeRoutes() ;
		if (--qe->retries) { // CHECK -> OK: packet retxmitted after SENDDONE_NOACK_WINDOW.
			trace()<<"SubSend.sendDone - not acked.";
			emit(registerSignal("CfeTxDoneNoAck"),self) ;
			startRetxmitTimer(SENDDONE_NOACK_WINDOW, SENDDONE_NOACK_OFFSET);
		} else { // CHECK -> OK: see inner statements
			//max retries, dropping packet
			collectOutput("Ctp Data","Tx Dropped - max retries") ;
			if (qe->client < CLIENT_COUNT) { // CHECK -> OK: packet dropped as expected.
				clientPtrs = qe ;
				delete qe->msg ; // Needed for OMNET++ : msg dup() in DualBuffer
				signal_Send_sendDone(FAIL) ;
				emit(registerSignal("CfeTxDoneDroppedMaxRetriesClient"),self) ;
				trace()<<"Subsend.sendDone - Max retries reached for client packet, dropping." ;
			} else { // CHECK -> OK: packet dropped as expected. No pools errors.
				trace()<<"Subsend.sendDone - Max retries reached for forwarded packet, dropping." ;
				emit(registerSignal("CfeTxDoneDroppedMacRetriesForwarded"),self) ;
				if(messagePool->command_Pool_put(qe->msg) != SUCCESS) trace()<<"Message pool error.";
				delete qe->msg ; // as stated in the forward function, the message is stored in another place than the messagePool, thus it must be deleted manually.
				if(qEntryPool->command_Pool_put(qe) != SUCCESS) trace()<<"QEntryPool error." ;
			}
			command_SendQueue_dequeue() ;
			sending = false;
			startRetxmitTimer(SENDDONE_OK_WINDOW, SENDDONE_OK_OFFSET);
		}
	}
	else if (qe->client < CLIENT_COUNT) { // CHECK -> OK: packet successfully txmitted and removed from queue.
		// there was a pointer to header that was never used... we have removed it.
		trace()<<"silviastats 1 "<<self<<" "<<(int)cre->command_Routing_nextHop()<<" "<<(int)command_CtpPacket_getOrigin(qe->msg)<<" "<<(int)command_CtpPacket_getSequenceNumber(qe->msg)<<" "<<(int)command_CtpPacket_getThl(qe->msg) ;
		emit(registerSignal("CfeTxDoneOkClient"),self) ;
		uint8_t client = qe->client;
		trace()<<"SubSend_sendDone - Our packet for client "<<(int)client<<" , remove from queue." ;
		le->command_LinkEstimator_txAck(command_AMPacket_destination(msg)) ;
		clientPtrs = qe ;
		delete qe->msg ; // Needed for OMNET++ : msg dup() in DualBuffer
		command_SendQueue_dequeue() ;
		signal_Send_sendDone(SUCCESS) ;
		sending = false;
		startRetxmitTimer(SENDDONE_OK_WINDOW, SENDDONE_OK_OFFSET);
	}
	else if(messagePool->command_Pool_size() < messagePool->command_Pool_maxSize()){ // CHECK -> OK: packet forwarded and no errors pools.
		// A successfully forwarded packet.
		trace()<<"silviastats 1 "<<self<<" "<<(int)cre->command_Routing_nextHop()<<" "<<(int)command_CtpPacket_getOrigin(qe->msg)<<" "<<(int)command_CtpPacket_getSequenceNumber(qe->msg)<<" "<<(int)command_CtpPacket_getThl(qe->msg) ;
		emit(registerSignal("CfeTxDoneOkForwarded"),self) ;
		trace()<<"SubSend.sendDone - successfully forwarded (client: "<<(int)qe->client<<") packet, message pool is "<<(int)messagePool->command_Pool_size()<<"/"<<(int)messagePool->command_Pool_maxSize() ;
		le->command_LinkEstimator_txAck(command_AMPacket_destination(msg)) ;
		command_SentCache_insert(qe->msg) ;
		command_SendQueue_dequeue() ;
		if(messagePool->command_Pool_put(qe->msg) != SUCCESS) trace()<<"MessagePool error."; // the message is still there (sentCache has a pointer to it), but can be overwritten, is it correct?
		if(qEntryPool->command_Pool_put(qe) != SUCCESS) trace()<<"QEntryPool error.";
		sending = false;
		startRetxmitTimer(SENDDONE_OK_WINDOW, SENDDONE_OK_OFFSET);
	}
	else {
		//      dbg("Forwarder", "%s: BUG: we have a pool entry, but the pool is full, client is %hhu.\n", __FUNCTION__, qe->client);
		opp_error("Bug2") ;
		// someone has double-stored a pointer somewhere and we have nowhere
		// to put this, so we have to leak it...
	}
}

uint8_t CtpForwardingEngine::getSeqNo(){
	return seqno ;
}


/*
 * Function for preparing a packet for forwarding. Performs
 * a buffer swap from the message pool. If there are no free
 * message in the pool, it returns the passed message and does not
 * put it on the send queue.
 */
void CtpForwardingEngine::forward(cPacket* msg){
	CtpData* m = check_and_cast<CtpData*>(msg) ;
	collectOutput("Ctp Data","Rx - forward total") ;
	if(messagePool->command_Pool_empty()){
		emit(registerSignal("CfeTxDroppedMessagePoolFull"),self) ;
		trace()<<"forward - cannot forward, message pool empty.";
	}
	else if(qEntryPool->command_Pool_empty()){
		emit(registerSignal("CfeTxDroppedQentryPoolFull"),self) ;
		trace()<<"forward - cannot forward, queue entry pool empty" ;
	}
	else {
		cPacket* newMsg ;
		fe_queue_entry_t *qe;
		uint16_t gradient;

		qe = qEntryPool->command_Pool_get() ;
		if (qe == NULL) {
			collectOutput("Ctp Data","Forward Dropped - qEntryPool full") ;
			emit(registerSignal("CfeTxDroppedQentryFull"),self) ;
			delete m ;
			return ;
		}

		/*
		 * IMPORTANT:
		 * The qEntryPool is used as it is done in TinyOs, but the messagePool is not
		 * needed actually.
		 * The message passed as argument in the forward function is owned by the module thus,
		 * it has its own memory allocation. We still keep the pool to simulate the tinyOs code.
		 * However, the value returned by the messagePool that is returned by the forward function is not used.
		 */
		newMsg = messagePool->command_Pool_get() ;
		if (newMsg == NULL) {
			collectOutput("Ctp Data","Forward Dropped - messagePool full") ;
			emit(registerSignal("CfeTxDroppedMessagePoolFull2"),self) ;
			delete m ;
			return ;
		}

		// There are two memset useless in our implementation: they have been removed

		qe->msg = m;
		qe->client = 0xff;
		qe->retries = MAX_RETRIES;

		if(command_SendQueue_enqueue(qe) == SUCCESS){
			trace()<<"forward - forwarding packet with queue size "<<(int)command_SendQueue_size() ;
			// Loop-detection code:
			if (cre->command_CtpInfo_getEtx(&gradient) == SUCCESS) {
				// We only check for loops if we know our own metric
				if (command_CtpPacket_getEtx(m) <= gradient ) {
					// If our etx metric is less than or equal to the etx value
					// on the packet (etx of the previous hop node), then we believe
					// we are in a loop.
					// Trigger a route update and backoff.
					trace()<<"Possible Loop Detection..." ;
					cre->command_CtpInfo_triggerImmediateRouteUpdate() ;
					startRetxmitTimer(LOOPY_WINDOW, LOOPY_OFFSET);
				}
			}

			if(! reTxTimerIsRunning){
				// sendTask is only immediately posted if we don't detect a
				// loop.
				post_sendTask() ;
			}

			// Successful function exit point:
			return ;
		} else {
			collectOutput("Ctp Data","Forward Dropped - sendQueue full") ;
			emit(registerSignal("CfeTxDroppedSendQueueFull"),self) ;

			// There was a problem enqueuing to the send queue.
			if(messagePool->command_Pool_put(newMsg) != SUCCESS) trace()<<"put pool error" ;
			delete qe->msg ;
			if(qEntryPool->command_Pool_put(qe) != SUCCESS) trace()<<"qentry put pool error" ;
		}
	}

	// NB: at this point, we have a resource acquistion problem.
	// Log the event, and drop the
	// packet on the floor.
	collectOutput("Ctp Data","Forward Dropped - pool empty") ;
	trace()<<"Resource Acquisition problem, drop packet...";
	delete msg ;
}

/*
 * Received a message to forward. Check whether it is a duplicate by
 * checking the packets currently in the queue as well as the
 * send history cache (in case we recently forwarded this packet).
 * The cache is important as nodes immediately forward packets
 * but wait a period before retransmitting after an ack failure.
 * If this node is a root, signal receive.
 */
void CtpForwardingEngine::event_SubReceive_receive(cPacket* pkt){
	collectOutput("Ctp Data","Rx total") ;

	trace()<<"silviastats 0 "<<self<<" "<<(int)command_AMPacket_source(pkt)<<" "<<(int)command_CtpPacket_getOrigin(pkt)<<" "<<(int)command_CtpPacket_getSequenceNumber(pkt)<<" "<<(int)command_CtpPacket_getThl(pkt) ;


	CtpData* msg = check_and_cast<CtpData*>(pkt) ;

	bool duplicate = false ;
	fe_queue_entry_t* qe;
	uint8_t i, thl;

	// Update the THL here, since it has lived another hop, and so
	// that the root sees the correct THL.
	thl = msg->getThl() ;
	thl++;
	msg->setThl(thl) ;

	//See if we remember having seen this packet
	//We look in the sent cache ...
	if(command_SentCache_lookup(msg)){
		trace()<<"Msg is in sentCache... deleting." ;
		collectOutput("Ctp Data","Rx Dropped - is in SentCache") ;
		delete msg ;
		return ;
	}
	//... and in the queue for duplicates
	if(command_SendQueue_size() > 0){
		for(i = command_SendQueue_size();--i;){
			qe = command_SendQueue_element(i) ;
			if (command_CtpPacket_matchInstance(qe->msg,msg)) {
				duplicate = true;
				break;
			}
		}
	}

	if (duplicate) {
		trace()<<"Msg is in SendQueue... deleting." ;
		collectOutput("Ctp Data","Rx Dropped - duplicated packet") ;
		delete msg ;
		return ;
	}

	// If I'm the root, signal receive.
	else if (cre->command_RootControl_isRoot()){
		collectOutput("Ctp Data","Rx - to app layer") ;
		trace()<<"I'm root, signaling app layer." ;
		// sends the packet to application layer.
		toApplicationLayer(msg->decapsulate()) ;
		delete msg ;
		return ;
	}
	// I'm on the routing path and Intercept indicates that I
	// should not forward the packet.

	// The Intercept interface is not provided in our implementation: it has been removed.
	else {
		trace()<<"Forwarding packet from "<<(int)getHeader(msg)->getOrigin() ;
		forward(msg) ;
	}
}

void CtpForwardingEngine::event_SubSnoop_receive(cPacket* pkt){
	CtpData* msg = check_and_cast<CtpData*>(pkt) ;
	trace()<<"Snooping packet..." ;
	uint16_t proximalSrc = command_AMPacket_source((cMessage*) pkt) ;

	// Check for the pull bit (P) [TEP123] and act accordingly.  This
	// check is made for all packets, not just ones addressed to us.
	if (command_CtpPacket_option(msg,CTP_OPT_PULL)) {
		cre->command_CtpInfo_triggerRouteUpdate() ;
	}

	cre->command_CtpInfo_setNeighborCongested(proximalSrc,command_CtpPacket_option(msg,CTP_OPT_ECN)) ;

	// The snoop interface is not provided to upper layer: the signal has been removed.
	collectOutput("Ctp Data","Snooped packet") ;
	delete pkt ;
}

void CtpForwardingEngine::event_RetxmitTimer_fired(){
	sending = false;
	post_sendTask() ;
}

void CtpForwardingEngine::event_CongestionTimer_fired(){
	post_sendTask() ;
}

// CtpCongestion interface -------------------------------------------------------------
bool CtpForwardingEngine::command_CtpCongestion_isCongested(){
	Enter_Method("command_CtpCongestion_isCongested") ;
	// A simple predicate for now to determine congestion state of
	// this node.
	bool congested = command_SendQueue_size() > congestionThreshold ? true:false ;
	return ((congested || clientCongested)? true:false) ;
}

void CtpForwardingEngine::command_CtpCongestion_setClientCongested(bool congested) {
	Enter_Method("command_CtpCongestion_setClientCongested") ;
	bool wasCongested = command_CtpCongestion_isCongested() ;
	clientCongested = congested;
	if (!wasCongested && congested) {
		cre->command_CtpInfo_triggerImmediateRouteUpdate() ;
	} else if(wasCongested && !command_CtpCongestion_isCongested()){
		cre->command_CtpInfo_triggerRouteUpdate() ;
	}
}
//---------------------------------------------------------------------------------------

// Packet interface -> SKIPPED, useless in our implementation ---------------------------
//command void Packet.clear(message_t* msg) {
//  call SubPacket.clear(msg);
//}
//
//command uint8_t Packet.payloadLength(message_t* msg) {
//  return call SubPacket.payloadLength(msg) - sizeof(ctp_data_header_t);
//}
//
//command void Packet.setPayloadLength(message_t* msg, uint8_t len) {
//  call SubPacket.setPayloadLength(msg, len + sizeof(ctp_data_header_t));
//}
//
//command uint8_t Packet.maxPayloadLength() {
//  return call SubPacket.maxPayloadLength() - sizeof(ctp_data_header_t);
//}
//
//command void* Packet.getPayload(message_t* msg, uint8_t len) {
//  uint8_t* payload = call SubPacket.getPayload(msg, len + sizeof(ctp_data_header_t));
//  if (payload != NULL) {
//    payload += sizeof(ctp_data_header_t);
//  }
//  return payload;
//}
// -----------------------------------------------------------------------------------------------

// CollectionPacket interface -> SKIPPED, we can use cPacket methods instead -----------------------
//  command am_addr_t       CollectionPacket.getOrigin(message_t* msg) {return getHeader(msg)->origin;}
//  command collection_id_t CollectionPacket.getType(message_t* msg) {return getHeader(msg)->type;}
//  command uint8_t         CollectionPacket.getSequenceNumber(message_t* msg) {return getHeader(msg)->originSeqNo;}
//  command void CollectionPacket.setOrigin(message_t* msg, am_addr_t addr) {getHeader(msg)->origin = addr;}
//  command void CollectionPacket.setType(message_t* msg, collection_id_t id) {getHeader(msg)->type = id;}
//  command void CollectionPacket.setSequenceNumber(message_t* msg, uint8_t _seqno) {getHeader(msg)->originSeqNo = _seqno;}
// --------------------------------------------------------------------------------------------------



// CtpPacket interface ---------------------------------------------------------------------------

// SKIPPED -> not used in our implementation.
//command ctp_options_t CtpPacket.getOptions(message_t* msg) {return getHeader(msg)->options;}

uint8_t CtpForwardingEngine::command_CtpPacket_getType(cPacket* pkt){return getHeader(pkt)->getType();}
uint16_t CtpForwardingEngine::command_CtpPacket_getOrigin(cPacket* pkt){return getHeader(pkt)->getOrigin();}
uint16_t CtpForwardingEngine::command_CtpPacket_getEtx(cPacket* pkt){ return getHeader(pkt)->getEtx(); }
uint8_t CtpForwardingEngine::command_CtpPacket_getSequenceNumber(cPacket* pkt){return getHeader(pkt)->getOriginSeqNo();}
uint8_t CtpForwardingEngine::command_CtpPacket_getThl(cPacket* pkt){return getHeader(pkt)->getThl();}

// SKIPPED -> not used in our implementation.
//  command void CtpPacket.setThl(message_t* msg, uint8_t thl) {getHeader(msg)->thl = thl;}
//  command void CtpPacket.setOrigin(message_t* msg, am_addr_t addr) {getHeader(msg)->origin = addr;}
//  command void CtpPacket.setType(message_t* msg, uint8_t id) {getHeader(msg)->type = id;}

bool CtpForwardingEngine::command_CtpPacket_option(cPacket* pkt, uint8_t opt){
	return ((getHeader(pkt)->getOptions() & opt) == opt) ? true:false ;
}

void CtpForwardingEngine::command_CtpPacket_setOption(cPacket* pkt, uint8_t opt){
	CtpData* msg = getHeader(pkt) ;
	uint8_t new_val = msg->getOptions() | opt ;
	msg->setOptions(new_val) ;
}

void CtpForwardingEngine::command_CtpPacket_clearOption(cPacket* pkt,uint8_t opt){
	CtpData* msg = getHeader(pkt) ;
	uint8_t new_val = msg->getOptions() & ~opt ;
	msg->setOptions(new_val) ;
}
void CtpForwardingEngine::command_CtpPacket_setEtx(cPacket* pkt,uint16_t e){
	CtpData* msg = check_and_cast<CtpData*>(pkt) ;
	msg->setEtx(e) ;
}

// SKIPPED -> not useful in our implementation.
//  command void CtpPacket.setSequenceNumber(message_t* msg, uint8_t _seqno) {getHeader(msg)->originSeqNo = _seqno;}

// A CTP packet ID is based on the origin and the THL field, to
// implement duplicate suppression as described in TEP 123.
bool CtpForwardingEngine::command_CtpPacket_matchInstance(cPacket* pkt1, cPacket* pkt2){
	return (command_CtpPacket_getOrigin(pkt1) == command_CtpPacket_getOrigin(pkt2) &&
			command_CtpPacket_getSequenceNumber(pkt1) == command_CtpPacket_getSequenceNumber(pkt2) &&
			command_CtpPacket_getThl(pkt1) == command_CtpPacket_getThl(pkt2) &&
			command_CtpPacket_getType(pkt1) == command_CtpPacket_getType(pkt2));
}

// SKIPPED -> not used in our implementation.
//  command bool CtpPacket.matchPacket(message_t* m1, message_t* m2) {
//    return (call CtpPacket.getOrigin(m1) == call CtpPacket.getOrigin(m2) &&
//	    call CtpPacket.getSequenceNumber(m1) == call CtpPacket.getSequenceNumber(m2) &&
//	    call CtpPacket.getType(m1) == call CtpPacket.getType(m2));
//  }

// --------------------------------------------------------------------------------------------------

// Default events -> SKIPPED except Send.sendDone(), not useful in our implementation. -------------------------------------

void CtpForwardingEngine::event_send_sendDone(uint8_t err) {
	Enter_Method("event_send_sendDone");
	trace()<<"SendDone! error: "<<(int)err;
}
//  default event bool
//  Intercept.forward[collection_id_t collectid](message_t* msg, void* payload,
//                                               uint8_t len) {
//    return TRUE;
//  }
//  default event message_t *
//  Receive.receive[collection_id_t collectid](message_t *msg, void *payload,
//                                             uint8_t len) {
//    return msg;
//  }
//  default event message_t *
//  Snoop.receive[collection_id_t collectid](message_t *msg, void *payload,
//                                           uint8_t len) {
//    return msg;
//  }
//  default command collection_id_t CollectionId.fetch[uint8_t client]() {
//    return 0;
//  }
// ----------------------------------------------------------------------------------------------------

void CtpForwardingEngine::startRetxmitTimer(uint16_t mask, uint16_t offset){
	uint16_t r = command_Random_rand16(0) ;
	r &= mask;
	r += offset;
	setTimer(RETXTIMER,tosMillisToSeconds(r)) ;
	reTxTimerIsRunning = true ;
	trace()<<"ReTxmitTimer - will fire in: "<<tosMillisToSeconds(r) ;
}

void CtpForwardingEngine::startCongestionTimer(uint16_t mask, uint16_t offset){
	uint16_t r = command_Random_rand16(0) ;
	r &= mask;
	r += offset;
	setTimer(CONGESTION_TIMER,tosMillisToSeconds(r)) ;
	congestionTimerIsRunning = true ;
	trace()<<"CongestionTimer - will fire in: "<<tosMillisToSeconds(r) ;

}

/* signalled when this neighbor is evicted from the neighbor table */
void CtpForwardingEngine::event_LinkEstimator_evicted(am_addr_t neighbor){

}

// SKIPPED -> CollectionDebug not implemented.
/* Default implementations for CollectionDebug calls.
 * These allow CollectionDebug not to be wired to anything if debugging
 * is not desired. */
//    default command error_t CollectionDebug.logEvent(uint8_t type) {
//        return SUCCESS;
//    }
//    default command error_t CollectionDebug.logEventSimple(uint8_t type, uint16_t arg) {
//        return SUCCESS;
//    }
//    default command error_t CollectionDebug.logEventDbg(uint8_t type, uint16_t arg1, uint16_t arg2, uint16_t arg3) {
//        return SUCCESS;
//    }
//    default command error_t CollectionDebug.logEventMsg(uint8_t type, uint16_t msg, am_addr_t origin, am_addr_t node) {
//        return SUCCESS;
//    }
//    default command error_t CollectionDebug.logEventRoute(uint8_t type, am_addr_t parent, uint8_t hopcount, uint16_t metric) {
//        return SUCCESS;
//    }

/* Rodrigo. This is an alternative
  event void CtpInfo.ParentCongested(bool congested) {
    if (congested) {
      // We've overheard our parent's ECN bit set.
      startCongestionTimer(CONGESTED_WAIT_WINDOW, CONGESTED_WAIT_OFFSET);
      parentCongested = TRUE;
      call CollectionDebug.logEvent(NET_C_FE_CONGESTION_BEGIN);
    } else {
      // We've overheard our parent's ECN bit cleared.
      call CongestionTimer.stop();
      parentCongested = FALSE;
      call CollectionDebug.logEventSimple(NET_C_FE_CONGESTION_END, 1);
      post sendTask();
    }
  }
*/


////////////////// Custom Functions //////////////////////////
//////////////////////////////////////////////////////////////

/*
 *  Schedule the sendTask function as soon as possible.
 *  Note that it is not possible to directly call the function
 *  because of the infinite recursion in the sendTask function.
 *  This implementation is even more similar to the post
 *  command in TinyOs
 */
void CtpForwardingEngine::post_sendTask(){
	setTimer(POST_SENDTASK,0) ;
}

// AMPacket interface (just what we need) -------------------------------------
uint16_t CtpForwardingEngine::command_AMPacket_address(){
	return (uint16_t) self ;
}

/*
 * We need the Mac source field that we do not have anymore since the packet has been decapsulated in the MAC.
 * The solution we found is to copy, in the mac layer, the source field in the standard routing
 * field named RoutingInteractionControl.lastHop field.
 */
uint16_t CtpForwardingEngine::command_AMPacket_source(cMessage* msg){
	RoutingPacket* rPkt = check_and_cast<RoutingPacket*>(msg) ;
	return (uint16_t) rPkt->getNetMacInfoExchange().lastHop ;
}

/*
 * This function is called in the SubReceive.sendDone() which, in our implementation, does not return the packet
 * as the original function do, rather a CC2420MacControlMessage.
 * The destination is stored in the MetaDest field of this header by the MAC layer.
 */
uint16_t CtpForwardingEngine::command_AMPacket_destination(cMessage* msg){
	CC2420MacControlMessage* cc2420control = check_and_cast<CC2420MacControlMessage*>(msg) ;
	return cc2420control->getMetaDest() ;
}
// ----------------------------------------------------------------------------

/*
 * Sets both, the standard routing fields provided by the routing packet and the
 * CtpData fields.
 */
void CtpForwardingEngine::encapsulatePacket(CtpData * netPkt, cPacket * appPkt)
{
	stringstream out;
	out << self;
	selfAddress = out.str();

	// Castalia standard routing fields.
	netPkt->setByteLength(ctpFeHeaderSize);
	netPkt->setKind(NETWORK_LAYER_PACKET);
	netPkt->setSource(selfAddress.c_str()) ; // ok
	netPkt->getNetMacInfoExchange().lastHop = self ; // ok

	// CTP Data fields
	netPkt->setOptions(netPkt->getOptions() | 0x01) ;
	netPkt->setOrigin((uint16_t) self) ;
	netPkt->setOriginSeqNo(seqno++) ;
	netPkt->setType(global_client);
	netPkt->setThl(0) ;
	netPkt->encapsulate(appPkt) ;
}

// SendQueue Interface -------------------------------------------------------
uint8_t CtpForwardingEngine::command_SendQueue_maxSize(){
	return queueMaxSize ;
}

bool CtpForwardingEngine::command_SendQueue_empty(){
	return sendqueue.empty() ;
}

error_t CtpForwardingEngine::command_SendQueue_enqueue(fe_queue_entry_t* qe){
	if(sendqueue.size() < queueMaxSize){
		sendqueue.push(qe) ;
		return SUCCESS ;
	}
	else return FAIL ;
}

uint8_t CtpForwardingEngine::command_SendQueue_size(){
	return sendqueue.size() ;
}

fe_queue_entry_t* CtpForwardingEngine::command_SendQueue_dequeue(){
	fe_queue_entry_t * ptr = sendqueue.front() ;
	sendqueue.pop() ;
	return ptr ;
}

fe_queue_entry_t* CtpForwardingEngine::command_SendQueue_element(uint8_t idx){
 		queue<fe_queue_entry_t*> searchQueue ;
		queue<fe_queue_entry_t*> bkpQueue ;
		fe_queue_entry_t* result ;

		while(sendqueue.size() != 0){
			searchQueue.push(sendqueue.front()) ;
			bkpQueue.push(sendqueue.front()) ;
			sendqueue.pop() ;
		}

		while(bkpQueue.size() != 0){
			sendqueue.push(bkpQueue.front()) ;
			bkpQueue.pop() ;
		}

		for(int i = 0; i<idx; i++){
			searchQueue.pop() ;
		}

		result = searchQueue.front() ;

		while(searchQueue.size() != 0){
			searchQueue.pop() ;
		}
		return result ;
}

fe_queue_entry_t* CtpForwardingEngine::command_SendQueue_head(){
	return sendqueue.front() ;
}
// ------------------------------------------------------------------------

// SentCache Interface ----------------------------------------------------
void CtpForwardingEngine::command_SentCache_insert(cPacket* pkt){
	if((uint8_t)sentCache.size() == sentCacheSize){ // remove the oldest element
		delete sentCache.front() ; // deletes the previously stored message.
		vector<cPacket*>::iterator eraseLocation = sentCache.begin();
		sentCache.erase(eraseLocation) ;
	}
	sentCache.push_back(pkt) ;
}

bool CtpForwardingEngine::command_SentCache_lookup(cPacket* pkt){
	int size = sentCache.size() ;
	for(int i=0 ; i<size ; i++){
		cPacket* actual_packet = (cPacket*) sentCache[i] ;

		if(command_CtpPacket_getOrigin(actual_packet) == command_CtpPacket_getOrigin(pkt) &&
				command_CtpPacket_getSequenceNumber(actual_packet) == command_CtpPacket_getSequenceNumber(pkt) &&
				command_CtpPacket_getThl(actual_packet) == command_CtpPacket_getThl(pkt) &&
				command_CtpPacket_getType(actual_packet) == command_CtpPacket_getType(pkt)) return true ;

	}
	return false ;

}

void CtpForwardingEngine::command_SentCache_flush(){
	sentCache.clear() ;
}
// ---------------------------------------------------------------------

// PacketAcknowledgement Interface (just what we need) ---------------------------------
bool CtpForwardingEngine::command_PacketAcknowledgements_wasAcked(cMessage* msg){
	CC2420MacControlMessage* cc2420control = check_and_cast<CC2420MacControlMessage*>(msg) ;
	return cc2420control->getMetaWasAcked() ;

}
// -------------------------------------------------------------------------------------

void CtpForwardingEngine::signal_Send_sendDone(error_t err){
	CtpNotification* ctpNot = new CtpNotification() ;
	ctpNot->setKind(NETWORK_CONTROL_MESSAGE) ;
	ctpNot->setCnType(EVENT) ;
	ctpNot->setCnInterface(SEND) ;
	ctpNot->setCnEvent(EVT_SENDDONE) ;
	ctpNot->setError(err) ;
	toApplicationLayer(ctpNot) ;
}

/*
 * Sends the packet to upper layer.
 */
void CtpForwardingEngine::toApplicationLayer(cMessage * msg){
	send(msg, "toCtp");
}


//////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////
