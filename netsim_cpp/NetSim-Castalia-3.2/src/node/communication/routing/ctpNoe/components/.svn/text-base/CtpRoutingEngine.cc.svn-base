/*
 * @author Ugo Colesanti
 * @author Silvia Santini
 * @version 1.02 (January 3, 2012)
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
  * Copyright (c) 2005 The Regents of the University  of California.  
  * All rights reserved.
  *
  * Permission to use, copy, modify, and distribute this software and its
  * documentation for any purpose, without fee, and without written agreement is
  * hereby granted, provided that the above copyright notice, the following
  * two paragraphs and the author appear in all copies of this software.
  * 
  * IN NO EVENT SHALL THE UNIVERSITY OF CALIFORNIA BE LIABLE TO ANY PARTY FOR
  * DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT
  * OF THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF THE UNIVERSITY OF
  * CALIFORNIA HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
  * 
  * THE UNIVERSITY OF CALIFORNIA SPECIFICALLY DISCLAIMS ANY WARRANTIES,
  * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
  * AND FITNESS FOR A PARTICULAR PURPOSE.  THE SOFTWARE PROVIDED HEREUNDER IS
  * ON AN "AS IS" BASIS, AND THE UNIVERSITY OF CALIFORNIA HAS NO OBLIGATION TO
  * PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS."
 */

#include "CtpRoutingEngine.h"
#include "CtpForwardingEngine.h"
#include "LinkEstimator.h"
Define_Module(CtpRoutingEngine);

void CtpRoutingEngine::initialize(){
	//////////////////////// Castalia Implementation ////////////////////
	/////////////////////////////////////////////////////////////////////

	//Pointers to other modules for direct function calls.
	cfe = check_and_cast<CtpForwardingEngine*>(getParentModule()->getSubmodule("CtpForwardingEngine")) ;
	le = check_and_cast<LinkEstimator*>(getParentModule()->getSubmodule("LinkEstimator")) ;

	//Id of the node (like TOS_NODE_ID)
	self = getParentModule()->getParentModule()->getParentModule()->getIndex();

	// The default values are set in CtpRoutingEngine.ned
	// but they can be overwritten in omnetpp.ini
	routingTableSize = par("routingTableSize"); // default 10 entries
	minInterval = par("minInterval"); // default 128
	maxInterval = par("maxInterval") ; // default 512000
	ctpReHeaderSize = par("ctpReHeaderSize") ; // default header size: 5 bytes
	isRoot = par("isRoot") ; // sets this node as root


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

	ECNOff = true;
	radioOn = true ; // TO IMPLEMENT ------ radioOn in stdcontrol
	running = false ;
	sending = false ;
	justEvicted = false ;

	routingTable = new routing_table_entry[routingTableSize] ;

	currentInterval = minInterval;

	/////////////////////////////////////////////////////////////////////
	/////////////////////////////////////////////////////////////////////

	/////////////////////////// Init.init() /////////////////////////////
	/////////////////////////////////////////////////////////////////////

	routeUpdateTimerCount = 0;
	parentChanges = 0;
	state_is_root = 0;

	routeInfoInit(&routeInfo);
	routingTableInit();
	my_ll_addr = command_AMPacket_address() ;

	beaconMsg = new CtpBeacon() ;
	beaconMsg->setByteLength(ctpReHeaderSize) ;

	// Call the corresponding rootcontrol command
	isRoot? command_RootControl_setRoot() : command_RootControl_unsetRoot() ;

	/////////////////////////////////////////////////////////////////////
	/////////////////////////////////////////////////////////////////////


	//////////////////////////////// Statistics /////////////////////////////////
	/////////////////////////////////////////////////////////////////////////////

	declareOutput("Ctp Beacons") ;

	/////////////////////////////////////////////////////////////////////////////
	/////////////////////////////////////////////////////////////////////////////
}

void CtpRoutingEngine::handleMessage(cMessage* msg){
	int msgKind = msg->getKind();
		switch (msgKind) {
	case TIMER_SERVICE:{
		handleTimerMessage(msg);
		break;
	}
	default:{
		opp_error("Unkown message type.") ;
	}
		}
		delete msg ;

}

void CtpRoutingEngine::timerFiredCallback(int timer)
{
	trace() << "CtpRE - TimerFiredCallback, value: "<<timer;
	switch (timer) {

		case ROUTE_TIMER:{
			setTimer(ROUTE_TIMER,tosMillisToSeconds(BEACON_INTERVAL)) ; // because it's a periodic timer.
			event_RouteTimer_fired() ;
			break;
		}
		case BEACON_TIMER:{
			event_BeaconTimer_fired() ;
			break;
		}
		case POST_UPDATEROUTETASK:{
			updateRouteTask() ;
			break ;
		}

		case POST_SENDBEACONTASK:{
			sendBeaconTask() ;
			break ;
		}


		default:{
			opp_error("Unexpected message!");
		}
	}
}

CtpRoutingEngine::~CtpRoutingEngine(){
	delete beaconMsg ;
	beaconMsg = NULL ;

	delete [] routingTable ;
	routingTable = NULL ;
}

void CtpRoutingEngine::chooseAdvertiseTime() {
	t = currentInterval;
	t /= 2;
	t += command_Random_rand32(1) % t;
	tHasPassed = false;
	setTimer(BEACON_TIMER,tosMillisToSeconds(t)) ;
}

void CtpRoutingEngine::resetInterval() {
  currentInterval = minInterval;
  chooseAdvertiseTime();
}

void CtpRoutingEngine::decayInterval() {
	currentInterval *= 2;
	if (currentInterval > maxInterval) {
		currentInterval = maxInterval;
	}
	chooseAdvertiseTime();
}

void CtpRoutingEngine::remainingInterval() {
   uint32_t remaining = currentInterval;
   remaining -= t;
   tHasPassed = true;
   setTimer(BEACON_TIMER,tosMillisToSeconds(remaining)) ;
}

error_t CtpRoutingEngine::command_StdControl_start() {
	Enter_Method("command_StdControl_start") ;
	//start will (re)start the sending of messages
	if (!running) {
		running = true;
		resetInterval();
		setTimer(ROUTE_TIMER,tosMillisToSeconds(BEACON_INTERVAL)) ;
		trace()<<"stdControl.start - running "<<running<<" radioOn: "<<radioOn ;
	}
	return SUCCESS;
}

error_t CtpRoutingEngine::command_StdControl_stop() {
	Enter_Method("command_StdControl_stop") ;
	running = false ;
	trace()<<"stdControl.stop - running "<<running<<" radioOn: "<<radioOn ;
	return SUCCESS;
}

void CtpRoutingEngine::event_RadioControl_startDone(error_t error) {
	Enter_Method("event_RadioControl_startDone") ;
	radioOn = true;
	trace()<<"radioControl.startDone - running "<<running<<" radioOn: "<<radioOn ;
	if (running) {
		uint16_t nextInt;
		nextInt = command_Random_rand16(0) % BEACON_INTERVAL ;
		nextInt += BEACON_INTERVAL >> 1;
		setTimer(BEACON_TIMER,tosMillisToSeconds(nextInt));
	}
}

void CtpRoutingEngine::event_RadioControl_stopDone(error_t error) {
	Enter_Method("event_RadioControl_stopDone") ;
	radioOn = false;
	trace()<<"radioControl.stopDone - running "<<running<<" radioOn: "<<radioOn ;

}

/* Is this quality measure better than the minimum threshold? */
// Implemented assuming quality is EETX
bool CtpRoutingEngine::passLinkEtxThreshold(uint16_t etx) {
	return true;
	//    	return (etx < ETX_THRESHOLD);
}

/* Converts the output of the link estimator to path metric
 * units, that can be *added* to form path metric measures */
uint16_t CtpRoutingEngine::evaluateEtx(uint16_t quality) {
	trace()<<"evaluateEtx - "<<(int) quality<<" -> "<<(int)(quality+10);
	return (quality + 10);
}


/* updates the routing information, using the info that has been received
 * from neighbor beacons. Two things can cause this info to change:
 * neighbor beacons, changes in link estimates, including neighbor eviction */
void CtpRoutingEngine::updateRouteTask() {
	uint8_t i;
	routing_table_entry* entry;
	routing_table_entry* best;
	uint16_t minEtx;
	uint16_t currentEtx;
	uint16_t linkEtx, pathEtx;

	if (state_is_root)
		return;

	best = NULL;
	/* Minimum etx found among neighbors, initially infinity */
	minEtx = MAX_METRIC;
	/* Metric through current parent, initially infinity */
	currentEtx = MAX_METRIC;

	trace()<<"updateRouteTask" ;

	/* Find best path in table, other than our current */
	for (i = 0; i < routingTableActive; i++) {
		entry = &routingTable[i];

		// Avoid bad entries and 1-hop loops
		if (entry->info.parent == INVALID_ADDR || entry->info.parent == my_ll_addr) {
			trace()<<"routingTable["<<(int)i<<"]: neighbor: [id: "<<(int)entry->neighbor<<" parent: "<<entry->info.parent<<"  etx: NO ROUTE]" ;
			continue;
		}
		/* Compute this neighbor's path metric */
		linkEtx = evaluateEtx(/*call LinkEstimator.getLinkQuality(entry->neighbor) changed with: */ le->command_LinkEstimator_getLinkQuality(entry->neighbor));
		trace()<<"routingTable["<<(int)i<<"]: neighbor: [id: "<<(int)entry->neighbor<<" parent: "<<entry->info.parent<<"  etx: "<<(int)linkEtx<<"]" ;
		pathEtx = linkEtx + entry->info.etx;
		/* Operations specific to the current parent */
		if (entry->neighbor == routeInfo.parent) {
			trace()<<"already parent";
			currentEtx = pathEtx;
			/* update routeInfo with parent's current info */
			routeInfo.etx = entry->info.etx;
			routeInfo.congested = entry->info.congested;
			continue;
		}
		/* Ignore links that are congested */
		if (entry->info.congested)
			continue;
		/* Ignore links that are bad */
		if (!passLinkEtxThreshold(linkEtx)) {
			trace()<<"did not pass threshold.";
			continue;
		}

		if (pathEtx < minEtx) {
			minEtx = pathEtx;
			best = entry;
		}
	}


	/* Now choose between the current parent and the best neighbor */
	/* Requires that:
            1. at least another neighbor was found with ok quality and not congested
            2. the current parent is congested and the other best route is at least as good
            3. or the current parent is not congested and the neighbor quality is better by
               the PARENT_SWITCH_THRESHOLD.
          Note: if our parent is congested, in order to avoid forming loops, we try to select
                a node which is not a descendent of our parent. routeInfo.ext is our parent's
                etx. Any descendent will be at least that + 10 (1 hop), so we restrict the
                selection to be less than that.
	 */
	if (minEtx != MAX_METRIC) {
		if (currentEtx == MAX_METRIC ||
				(routeInfo.congested && (minEtx < (routeInfo.etx + 10))) ||
				minEtx + PARENT_SWITCH_THRESHOLD < currentEtx) {
			// routeInfo.metric will not store the composed metric.
			// since the linkMetric may change, we will compose whenever
			// we need it: i. when choosing a parent (here);
			//            ii. when choosing a next hop
			parentChanges++;

			trace()<<"Changed parent. from "<<(int)routeInfo.parent<<" to "<<(int)best->neighbor;
			le->command_LinkEstimator_unpinNeighbor(routeInfo.parent) ;
			le->command_LinkEstimator_pinNeighbor(best->neighbor) ;
			le->command_LinkEstimator_clearDLQ(best->neighbor) ;

			routeInfo.parent = best->neighbor;
			routeInfo.etx = best->info.etx;
			routeInfo.congested = best->info.congested;
		}
	}

	/* Finally, tell people what happened:  */
	/* We can only loose a route to a parent if it has been evicted. If it hasn't
	 * been just evicted then we already did not have a route */
	if (justEvicted && routeInfo.parent == INVALID_ADDR)
		signal_Routing_noRoute() ;
	/* On the other hand, if we didn't have a parent (no currentEtx) and now we
	 * do, then we signal route found. The exception is if we just evicted the
	 * parent and immediately found a replacement route: we don't signal in this
	 * case */
	else if (!justEvicted &&
			currentEtx == MAX_METRIC &&
			minEtx != MAX_METRIC)
		signal_Routing_routeFound() ;
	justEvicted = false;
}

/* send a beacon advertising this node's routeInfo */
// only posted if running and radioOn
void CtpRoutingEngine::sendBeaconTask() {
	error_t eval;
	if (sending) {
		return;
	}

	beaconMsg->setOptions(0) ;

	/* Congestion notification: am I congested? */
	if (cfe->command_CtpCongestion_isCongested()) {
		beaconMsg->setOptions(beaconMsg->getOptions() | CTP_OPT_ECN) ;
	}

	beaconMsg->setParent(routeInfo.parent) ;
	if (state_is_root) {
		beaconMsg->setEtx(routeInfo.etx) ;
	}
	else if (routeInfo.parent == INVALID_ADDR) {
		beaconMsg->setEtx(routeInfo.etx) ;
		beaconMsg->setOptions(beaconMsg->getOptions() | CTP_OPT_PULL) ;
	} else {
		beaconMsg->setEtx(routeInfo.etx + evaluateEtx(le->command_LinkEstimator_getLinkQuality(routeInfo.parent))) ;
	}

	trace()<<"sendBeaconTask - parent: "<<(int)beaconMsg->getParent()<<" etx: "<<(int)beaconMsg->getEtx();

	beaconMsg->getNetMacInfoExchange().lastHop = self ; // ok
	eval = le->command_Send_send(AM_BROADCAST_ADDR,beaconMsg->dup()); // the duplicate will be deleted in the LE module, we keep a copy here that is reused each time.

	if (eval == SUCCESS) {
		//statistics
		emit(registerSignal("BeaconTx"),self) ;
		collectOutput("Ctp Beacons","Tx") ;
		sending = true;
	} else if (eval == EOFF) {
		radioOn = false;
		trace()<<"sendBeaconTask - running: "<<running<<" radioOn: "<<radioOn ;
	}
}

void CtpRoutingEngine::event_BeaconSend_sendDone(cMessage* msg, error_t error) {
	Enter_Method("event_BeaconSend_sendDone") ;
	if (!sending) {
		//something smells bad around here
		opp_error("something smells bad around here");
		return;
	}
	sending = false;
}

void CtpRoutingEngine::event_RouteTimer_fired() {
	if (radioOn && running) {
		post_updateRouteTask() ;
	}
}

void CtpRoutingEngine::event_BeaconTimer_fired() {
	if (radioOn && running) {
		if (!tHasPassed) {
			post_updateRouteTask() ; // always the most up to date info
			post_sendBeaconTask() ;
			trace()<<"Beacon timer fired.";
			remainingInterval();
		}
		else {
			decayInterval();
		}
	}
}

/*
 * We don't need a pointer to the header, we can use the methods of cPacket
 * instead, we return a pointer to CtpBeacon and that's it.
 */
CtpBeacon* CtpRoutingEngine::getHeader(cPacket* msg){
	return check_and_cast<CtpBeacon*>(msg) ;
}

/* Handle the receiving of beacon messages from the neighbors. We update the
 * table, but wait for the next route update to choose a new parent */
void CtpRoutingEngine::event_BeaconReceive_receive(cPacket* msg) {
	Enter_Method("event_BeaconReceive_receive") ;
	am_addr_t from;
	bool congested;

	//statistics
	collectOutput("Ctp Beacons","Rx") ;

	// we skip the check of beacon length.

	//need to get the am_addr_t of the source
	from = command_AMPacket_source(msg) ;

	//statistics
	beaconRx brx;
	brx.id = self ;
	brx.from = from ;
	emit(registerSignal("BeaconRx"),&brx) ;


	CtpBeacon* rcvBeacon = check_and_cast<CtpBeacon*>(msg) ;

	congested = command_CtpRoutingPacket_getOption(msg,CTP_OPT_ECN) ;

	trace()<<"BeaconReceive.receive - from "<<(int)from<<" [parent: "<<(int)rcvBeacon->getParent()<<" etx: "<<(int)rcvBeacon->getEtx()<<"]";
	//update neighbor table
	if (rcvBeacon->getParent() != INVALID_ADDR) {

		/* If this node is a root, request a forced insert in the link
		 * estimator table and pin the node. */
		if (rcvBeacon->getEtx() == 0) {
			trace()<<"from a root, inserting if not in table";
			le->command_LinkEstimator_insertNeighbor(from) ;
			le->command_LinkEstimator_pinNeighbor(from) ;
		}
		//TODO: also, if better than my current parent's path etx, insert

		routingTableUpdateEntry(from, rcvBeacon->getParent(), rcvBeacon->getEtx());
		command_CtpInfo_setNeighborCongested(from,congested) ;
	}

	if (command_CtpRoutingPacket_getOption(msg, CTP_OPT_PULL)) {
		resetInterval();
	}
	delete msg ;
	// we do not return the message, we delete it.
}

/* Signals that a neighbor is no longer reachable. need special care if
 * that neighbor is our parent */
void CtpRoutingEngine::event_LinkEstimator_evicted(am_addr_t neighbor) {
	Enter_Method("event_LinkEstimator_evicted") ;
	routingTableEvict(neighbor);
	trace()<<"LinkEstimator.evicted" ;
	if (routeInfo.parent == neighbor) {
		routeInfoInit(&routeInfo);
		justEvicted = true;
		post_updateRouteTask() ;
	}
}

/*
 * UnicastNameFreeRouting Inteface -----------------------------------------
 */
/* Simple implementation: return the current routeInfo */
am_addr_t CtpRoutingEngine::command_Routing_nextHop() {
	Enter_Method("command_Routing_nextHop") ;
	return routeInfo.parent;
}
bool CtpRoutingEngine::command_Routing_hasRoute() {
	Enter_Method("command_Routing_hasRoute") ;
	return (routeInfo.parent != INVALID_ADDR);
}
// -------------------------------------------------------------------------

/*
 * CtpInfo Interface (Part 1) ----------------------------------------------------------------
 */
error_t CtpRoutingEngine::command_CtpInfo_getParent(am_addr_t* parent) {
	if (parent == NULL)
		return FAIL;
	if (routeInfo.parent == INVALID_ADDR)
		return FAIL;
	*parent = routeInfo.parent;
	return SUCCESS;
}

error_t CtpRoutingEngine::command_CtpInfo_getEtx(uint16_t* etx) {
	Enter_Method("command_CtpInfo_getEtx") ;
	if (etx == NULL)
		return FAIL;
	if (routeInfo.parent == INVALID_ADDR)
		return FAIL;
	if (state_is_root == 1) {
		*etx = 0;
	} else {
		// path etx = etx(parent) + etx(link to the parent)
		*etx = routeInfo.etx + evaluateEtx(le->command_LinkEstimator_getLinkQuality(routeInfo.parent) );
	}
	return SUCCESS;
}

void CtpRoutingEngine::command_CtpInfo_recomputeRoutes() {
	Enter_Method("command_CtpInfo_recomputeRoutes") ;
	post_updateRouteTask() ;
}

void CtpRoutingEngine::command_CtpInfo_triggerRouteUpdate() {
	Enter_Method("command_CtpInfo_triggerRouteUpdate") ;
	resetInterval();
}

void CtpRoutingEngine::command_CtpInfo_triggerImmediateRouteUpdate() {
	Enter_Method("command_CtpInfo_triggerImmediateRouteUpdate") ;
	resetInterval();
}

void CtpRoutingEngine::command_CtpInfo_setNeighborCongested(am_addr_t n, bool congested) {
	Enter_Method("command_CtpInfo_setNeighborCongested") ;
	uint8_t idx;
	if (ECNOff)
		return;
	idx = routingTableFind(n);
	if (idx < routingTableActive) {
		routingTable[idx].info.congested = congested;
	}
	if (routeInfo.congested && !congested)
		post_updateRouteTask() ;
	else if (routeInfo.parent == n && congested)
		post_updateRouteTask() ;
}

bool CtpRoutingEngine::command_CtpInfo_isNeighborCongested(am_addr_t n) {
	Enter_Method("command_CtpInfo_isNeighborCongested") ;
	uint8_t idx;

	if (ECNOff)
		return false;

	idx = routingTableFind(n);
	if (idx < routingTableActive) {
		return routingTable[idx].info.congested;
	}
	return false;
}
// ----------------------------------------------------------------------------------

/*
 *  RootControl Interface -----------------------------------------------------------
 */
/** sets the current node as a root, if not already a root */
/*  returns FAIL if it's not possible for some reason      */
error_t CtpRoutingEngine::command_RootControl_setRoot() {
	Enter_Method("command_RootControl_setRoot") ;
	bool route_found = false ;
	route_found = (routeInfo.parent == INVALID_ADDR);
	state_is_root = 1;
	routeInfo.parent = my_ll_addr; //myself
	routeInfo.etx = 0;
	if (route_found)
		signal_Routing_routeFound() ;
	trace()<<"RootControl.setRoot - I'm a root now!"<<(int) routeInfo.parent  ;
	return SUCCESS;
}

error_t CtpRoutingEngine::command_RootControl_unsetRoot() {
	Enter_Method("command_RootControl_unsetRoot") ;
	state_is_root = 0;
	routeInfoInit(&routeInfo);
	trace()<<"RootControl.unsetRoot - I'm not a root now!" ;
	post_updateRouteTask() ;
	return SUCCESS;
}

bool CtpRoutingEngine::command_RootControl_isRoot() {
	Enter_Method("command_RootControl_isRoot") ;
	return state_is_root;
}
// -----------------------------------------------------------------------------------

// default events Routing.noRoute and Routing.routeFound skipped -> useless

/* This should see if the node should be inserted in the table.
 * If the white_bit is set, this means the LL believes this is a good
 * first hop link.
 * The link will be recommended for insertion if it is better* than some
 * link in the routing table that is not our parent.
 * We are comparing the path quality up to the node, and ignoring the link
 * quality from us to the node. This is because of a couple of things:
 *   1. because of the white bit, we assume that the 1-hop to the candidate
 *      link is good (say, etx=1)
 *   2. we are being optimistic to the nodes in the table, by ignoring the
 *      1-hop quality to them (which means we are assuming it's 1 as well)
 *      This actually sets the bar a little higher for replacement
 *   3. this is faster
 *   4. it doesn't require the link estimator to have stabilized on a link
 */
bool CtpRoutingEngine::event_CompareBit_shouldInsert(cPacket *msg, bool white_bit) {
	Enter_Method("event_CompareBit_shouldInsert") ;
	bool found = false;
	uint16_t pathEtx;
	uint16_t neighEtx;
	int i;
	routing_table_entry* entry;
	CtpBeacon* rcvBeacon ;

	// checks if it is a CtpBeacon
	if(dynamic_cast<CtpBeacon*>(msg) == NULL){
		delete msg ;
		return false ;
	}

	/* 1.determine this packet's path quality */
	rcvBeacon = check_and_cast<CtpBeacon*>(msg); // we don't need a pointer to header, we use cPacket methods.

	if (rcvBeacon->getParent() == INVALID_ADDR){
		delete msg ;
		return false;
	}

	/* the node is a root, recommend insertion! */
	if (rcvBeacon->getEtx() == 0) {
		delete msg ;
		return true;
	}

	pathEtx = rcvBeacon->getEtx() ;

	/* 2. see if we find some neighbor that is worse */
	for (i = 0; i < routingTableActive && !found; i++) {
		entry = &routingTable[i];
		//ignore parent, since we can't replace it
		if (entry->neighbor == routeInfo.parent)
			continue;
		neighEtx = entry->info.etx;
		//neighEtx = evaluateEtx(call LinkEstimator.getLinkQuality(entry->neighbor));
		found |= (pathEtx < neighEtx);
	}
	delete msg ;
	return found;
}

/************************************************************/
/* Routing Table Functions                                  */

/* The routing table keeps info about neighbor's route_info,
 * and is used when choosing a parent.
 * The table is simple:
 *   - not fragmented (all entries in 0..routingTableActive)
 *   - not ordered
 *   - no replacement: eviction follows the LinkEstimator table
 */

void CtpRoutingEngine::routingTableInit() {
	routingTableActive = 0;
}

/* Returns the index of parent in the table or
 * routingTableActive if not found */
uint8_t CtpRoutingEngine::routingTableFind(am_addr_t neighbor) {
	uint8_t i;
	if (neighbor == INVALID_ADDR)
		return routingTableActive;
	for (i = 0; i < routingTableActive; i++) {
		if (routingTable[i].neighbor == neighbor)
			break;
	}
	return i;
}


error_t CtpRoutingEngine::routingTableUpdateEntry(am_addr_t from, am_addr_t parent, uint16_t etx)    {
	uint8_t idx;
	uint16_t  linkEtx;
	linkEtx = evaluateEtx(le->command_LinkEstimator_getLinkQuality(from));

	idx = routingTableFind(from);
	if (idx == routingTableSize) {
		//not found and table is full
		//if (passLinkEtxThreshold(linkEtx))
		//TODO: add replacement here, replace the worst
		//}
		trace()<<"routingTableUpdateEntry - FAIL, table full";
		return FAIL;
	}
	else if (idx == routingTableActive) {
		//not found and there is space
		if (passLinkEtxThreshold(linkEtx)) {
			routingTable[idx].neighbor = from;
			routingTable[idx].info.parent = parent;
			routingTable[idx].info.etx = etx;
			routingTable[idx].info.haveHeard = 1;
			routingTable[idx].info.congested = false;
			routingTableActive++;
			trace()<<"routingTableUpdateEntry - OK, new entry";
		} else {
			trace()<<"routingTableUpdateEntry - Fail, link quality ("<<(int)linkEtx<<") below threshold" ;
		}
	} else {
		//found, just update
		routingTable[idx].neighbor = from;
		routingTable[idx].info.parent = parent;
		routingTable[idx].info.etx = etx;
		routingTable[idx].info.haveHeard = 1;
		trace()<<"routingTableUpdateEntry - OK, updated entry";
	}
	return SUCCESS;
}

/* if this gets expensive, introduce indirection through an array of pointers */
error_t CtpRoutingEngine::routingTableEvict(am_addr_t neighbor) {
	uint8_t idx,i;
	idx = routingTableFind(neighbor);
	if (idx == routingTableActive)
		return FAIL;
	routingTableActive--;
	for (i = idx; i < routingTableActive; i++) {
		routingTable[i] = routingTable[i+1];
	}
	return SUCCESS;
}
/*********** end routing table functions ***************/

// Collection Debug skipped -> not useful in our implementation

/*
 * CtpRoutingPacket Interface ---------------------------------------------------------------------
 */
bool CtpRoutingEngine::command_CtpRoutingPacket_getOption(cPacket* msg, ctp_options_t opt) {
	return ((getHeader(msg)->getOptions() & opt) == opt) ? true : false;
}

void CtpRoutingEngine::command_CtpRoutingPacket_setOption(cPacket* msg, ctp_options_t opt) {
	getHeader(msg)->setOptions(getHeader(msg)->getOptions() | opt) ;
}

void CtpRoutingEngine::command_CtpRoutingPacket_clearOption(cPacket* msg, ctp_options_t opt) {
	getHeader(msg)->setOptions(getHeader(msg)->getOptions() & ~opt) ;
}

void CtpRoutingEngine::command_CtpRoutingPacket_clearOptions(cPacket* msg) {
	getHeader(msg)->setOptions(0) ;
}

am_addr_t CtpRoutingEngine::command_CtpRoutingPacket_getParent(cPacket* msg) {
	return getHeader(msg)->getParent();
}
void CtpRoutingEngine::command_CtpRoutingPacket_setParent(cPacket* msg, am_addr_t addr) {
	getHeader(msg)->setParent(addr);
}

uint16_t CtpRoutingEngine::command_CtpRoutingPacket_getEtx(cPacket* msg) {
	return getHeader(msg)->getEtx();
}

void CtpRoutingEngine::command_CtpRoutingPacket_setEtx(cPacket* msg, uint8_t etx) {
	getHeader(msg)->setEtx(etx);
}
// -------------------------------------------------------------------------------------------------

/*
 * CtpInfo Interface (Part 2) ----------------------------------------------------------------------
 */
uint8_t CtpRoutingEngine::command_CtpInfo_numNeighbors() {
	return routingTableActive;
}

uint16_t CtpRoutingEngine::command_CtpInfo_getNeighborLinkQuality(uint8_t n) {
	return (n < routingTableActive)? le->command_LinkEstimator_getLinkQuality(routingTable[n].neighbor):0xffff;
}

uint16_t CtpRoutingEngine::command_CtpInfo_getNeighborRouteQuality(uint8_t n) {
	return (n < routingTableActive)? le->command_LinkEstimator_getLinkQuality(routingTable[n].neighbor) + routingTable[n].info.etx:0xfffff;
}

am_addr_t CtpRoutingEngine::command_CtpInfo_getNeighborAddr(uint8_t n) {
	return (n < routingTableActive)? routingTable[n].neighbor:AM_BROADCAST_ADDR ;
}
// --------------------------------------------------------------------------------------------------


//////////////////////////// Custom functions /////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////

// These functions trigger an event in the module where they should signal it.
void CtpRoutingEngine::signal_Routing_routeFound(){
	cfe->event_UnicastNameFreeRouting_routeFound() ;
}
void CtpRoutingEngine::signal_Routing_noRoute(){
	cfe->event_UnicastNameFreeRouting_routeFound() ;
}

/*
 * AMPacket Interface (just what we need) ------------------------------------
 */
am_addr_t CtpRoutingEngine::command_AMPacket_source(cMessage* msg){
	RoutingPacket* rPkt = check_and_cast<RoutingPacket*>(msg) ;
	return (uint16_t) rPkt->getNetMacInfoExchange().lastHop ;
}

am_addr_t CtpRoutingEngine::command_AMPacket_address(){
	return self ;
}
// ---------------------------------------------------------------------------

// these functions simulate the post command of TinyOs
void CtpRoutingEngine::post_updateRouteTask(){
	setTimer(POST_UPDATEROUTETASK,0); // cannot call the updateRouteTask directly. By this way it is more similar to the post command in TinyOs.
}

void CtpRoutingEngine::post_sendBeaconTask(){
	setTimer(POST_SENDBEACONTASK,0) ;
}

///////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////
