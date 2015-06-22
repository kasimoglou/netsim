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
 * "Copyright (c) 2006 University of Southern California.
 * All rights reserved.
 *
 * Permission to use, copy, modify, and distribute this software and its
 * documentation for any purpose, without fee, and without written
 * agreement is hereby granted, provided that the above copyright
 * notice, the following two paragraphs and the author appear in all
 * copies of this software.
 *
 * IN NO EVENT SHALL THE UNIVERSITY OF SOUTHERN CALIFORNIA BE LIABLE TO
 * ANY PARTY FOR DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL
 * DAMAGES ARISING OUT OF THE USE OF THIS SOFTWARE AND ITS
 * DOCUMENTATION, EVEN IF THE UNIVERSITY OF SOUTHERN CALIFORNIA HAS BEEN
 * ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * THE UNIVERSITY OF SOUTHERN CALIFORNIA SPECIFICALLY DISCLAIMS ANY
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE SOFTWARE
 * PROVIDED HEREUNDER IS ON AN "AS IS" BASIS, AND THE UNIVERSITY OF
 * SOUTHERN CALIFORNIA HAS NO OBLIGATION TO PROVIDE MAINTENANCE,
 * SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS."
 */

#include "LinkEstimator.h"
#include "CtpRoutingEngine.h"
#include "DualBuffer.h"
Define_Module(LinkEstimator);

void LinkEstimator::initialize(){

	//////////////////////// Castalia Implementation ////////////////////
	/////////////////////////////////////////////////////////////////////

	//Pointers to other modules for direct function calls.
	db = check_and_cast<DualBuffer*>(getParentModule()->getSubmodule("DualBuffer")) ;
	cre = check_and_cast<CtpRoutingEngine*>(getParentModule()->getSubmodule("CtpRoutingEngine")) ;

	//Id of the node (like TOS_NODE_ID)
	self = getParentModule()->getParentModule()->getParentModule()->getIndex();

	// The default values are set in LinkEstimator.ned
	// but they can be overwritten in the omnetpp.ini
	NEIGHBOR_TABLE_SIZE = par("neighborTableSize") ; // size of the link estimator neighbor table (default 10 entries)
	ctpLeHeaderSize = par("ctpLeHeaderSize") ; // size of the link estimator header (default 2 bytes)

	///////////////////// CtpForwardingEngine (default) /////////////////
	/////////////////////////////////////////////////////////////////////

	NeighborTable = new neighbor_table_entry_t[NEIGHBOR_TABLE_SIZE] ;
	linkEstSeq = 0 ;
	prevSentIdx = 0 ;

	/////////////////////////////////////////////////////////////////////
	/////////////////////////////////////////////////////////////////////

	/////////////////////////// Init.init() /////////////////////////////
	/////////////////////////////////////////////////////////////////////

	initNeighborTable();

	/////////////////////////////////////////////////////////////////////
	/////////////////////////////////////////////////////////////////////

}

void LinkEstimator::handleMessage(cMessage * msg){
	int msgKind = msg->getKind();
	switch (msgKind) {
		case NETWORK_LAYER_PACKET:{
			CtpLe *lePkt = check_and_cast <CtpLe*>(msg);
			event_SubReceive_receive(lePkt) ;
			return ;
		}
	}

	delete msg ;
}

LinkEstimator::~LinkEstimator(){
	delete [] NeighborTable ;
	NeighborTable = NULL ;
}

/*
 * getHeader and getFooter are skipped, we use methods of cPacket instead.
 */

//// get the link estimation header in the packet
//linkest_header_t* getHeader(message_t* m) {
//	return (linkest_header_t*)call SubPacket.getPayload(m, sizeof(linkest_header_t));
//}
//
//// get the link estimation footer (neighbor entries) in the packet
//linkest_footer_t* getFooter(message_t* m, uint8_t len) {
//	// To get a footer at offset "len", the payload must be len + sizeof large.
//	return (linkest_footer_t*)(len + (uint8_t *)call Packet.getPayload(m,len + sizeof(linkest_footer_t)));
//}

// add the link estimation header (seq no) and link estimation
// footer (neighbor entries) in the packet. Call just before sending
// the packet.
uint8_t LinkEstimator::addLinkEstHeaderAndFooter(CtpLe *msg,uint8_t len) {

	// header and footer operations are skipped, we use cPacket methods instead.

	uint8_t i, j, k;
	uint8_t maxEntries, newPrevSentIdx;

	maxEntries = ((TOSH_DATA_LENGTH - len - ctpLeHeaderSize) / sizeof(neighbor_stat_entry) ) ;

	// Depending on the number of bits used to store the number
	// of entries, we can encode up to NUM_ENTRIES_FLAG using those bits
	if (maxEntries > NUM_ENTRIES_FLAG) {
		maxEntries = NUM_ENTRIES_FLAG;
	}
	trace()<<"Max payload is: "<<TOSH_DATA_LENGTH<<", maxEntries is: "<<(int)maxEntries;

	j = 0;
	newPrevSentIdx = 0;

	// In CtpNoePacket.msg we have defined a footer as an array of neighbor_stat_entry.
	// Before storing any valu, we need to determine the size of the array.
	// To this aim the first for loop just counts the number of entries that will be
	// stored in the footer while the second loop actually stores them.
	for (i = 0; i < NEIGHBOR_TABLE_SIZE && j < maxEntries; i++) {
		uint8_t neighborCount;

		if(maxEntries <= NEIGHBOR_TABLE_SIZE)
			neighborCount = maxEntries;
		else
			neighborCount = NEIGHBOR_TABLE_SIZE;

		k = (prevSentIdx + i + 1) % NEIGHBOR_TABLE_SIZE;
		if ((NeighborTable[k].flags & VALID_ENTRY) &&
				(NeighborTable[k].flags & MATURE_ENTRY)) {
			j++;
		}
	}

	msg->setLinkest_footerArraySize(j) ;
	j = 0 ;

	for (i = 0; i < NEIGHBOR_TABLE_SIZE && j < maxEntries; i++) {
		uint8_t neighborCount;
		if(maxEntries <= NEIGHBOR_TABLE_SIZE)
			neighborCount = maxEntries;
		else
			neighborCount = NEIGHBOR_TABLE_SIZE;

		k = (prevSentIdx + i + 1) % NEIGHBOR_TABLE_SIZE;
		if ((NeighborTable[k].flags & VALID_ENTRY) &&
				(NeighborTable[k].flags & MATURE_ENTRY)) {

			neighbor_stat_entry temp ;
			temp.ll_addr = NeighborTable[k].ll_addr;
			temp.inquality = NeighborTable[k].inquality;
			msg->setLinkest_footer(j,temp) ;
			newPrevSentIdx = k;

			trace()<<"Loaded on footer: "<<(int)j<<" "<<(int)temp.ll_addr<<" "<<(int)temp.inquality ;
			j++;
		}
	}
	prevSentIdx = newPrevSentIdx;

	msg->setSeq(linkEstSeq++) ;
	msg->setFlags(0 | (NUM_ENTRIES_FLAG & j)) ;
	return ctpLeHeaderSize + j*sizeof(neighbor_stat_entry);
}

// initialize the given entry in the table for neighbor ll_addr
void LinkEstimator::initNeighborIdx(uint8_t i, am_addr_t ll_addr) {
	neighbor_table_entry_t *ne;
	ne = &NeighborTable[i];
	ne->ll_addr = ll_addr;
	ne->lastseq = 0;
	ne->rcvcnt = 0;
	ne->failcnt = 0;
	ne->flags = (INIT_ENTRY | VALID_ENTRY);
	ne->inage = MAX_AGE;
	ne->inquality = 0;
	ne->eetx = 0;
}

// find the index to the entry for neighbor ll_addr
uint8_t LinkEstimator::findIdx(am_addr_t ll_addr) {
	uint8_t i;
	for (i = 0; i < NEIGHBOR_TABLE_SIZE; i++) {
		if (NeighborTable[i].flags & VALID_ENTRY) {
			if (NeighborTable[i].ll_addr == ll_addr) {
				return i;
			}
		}
	}
	return INVALID_RVAL;
}

// find an empty slot in the neighbor table
uint8_t LinkEstimator::findEmptyNeighborIdx() {
	uint8_t i;
	for (i = 0; i < NEIGHBOR_TABLE_SIZE; i++) {
		if (NeighborTable[i].flags & VALID_ENTRY) {
		} else {
			return i;
		}
	}
	return INVALID_RVAL;
}

// find the index to the worst neighbor if the eetx
// estimate is greater than the given threshold
uint8_t LinkEstimator::findWorstNeighborIdx(uint8_t thresholdEETX) {
	uint8_t i, worstNeighborIdx;
	uint16_t worstEETX, thisEETX;

	worstNeighborIdx = INVALID_RVAL;
	worstEETX = 0;
	for (i = 0; i < NEIGHBOR_TABLE_SIZE; i++) {
		if (!(NeighborTable[i].flags & VALID_ENTRY)) {
			trace()<<"Invalid so continuing";
			continue;
		}
		if (!(NeighborTable[i].flags & MATURE_ENTRY)) {
			trace()<<"Not mature, so continuing";
			continue;
		}
		if (NeighborTable[i].flags & PINNED_ENTRY) {
			trace()<<"Pinned entry, so continuing";
			continue;
		}
		thisEETX = NeighborTable[i].eetx;
		if (thisEETX >= worstEETX) {
			worstNeighborIdx = i;
			worstEETX = thisEETX;
		}
	}
	if (worstEETX >= thresholdEETX) {
		return worstNeighborIdx;
	} else {
		return INVALID_RVAL;
	}
}

// find the index to a random entry that is
// valid but not pinned
uint8_t LinkEstimator::findRandomNeighborIdx() {
	uint8_t i;
	uint8_t cnt;
	uint8_t num_eligible_eviction;

	num_eligible_eviction = 0;
	for (i = 0; i < NEIGHBOR_TABLE_SIZE; i++) {
		if (NeighborTable[i].flags & VALID_ENTRY) {
			if (NeighborTable[i].flags & PINNED_ENTRY ||
					NeighborTable[i].flags & MATURE_ENTRY) {
			}  else {
				num_eligible_eviction++;
			}
		}
	}

	if (num_eligible_eviction == 0) {
		return INVALID_RVAL;
	}

	cnt = command_Random_rand16(0) % num_eligible_eviction ;

	for (i = 0; i < NEIGHBOR_TABLE_SIZE; i++) {
		if (!NeighborTable[i].flags & VALID_ENTRY)
			continue;
		if (NeighborTable[i].flags & PINNED_ENTRY ||
				NeighborTable[i].flags & MATURE_ENTRY)
			continue;
		if (cnt-- == 0)
			return i;
	}
	return INVALID_RVAL;
}

// update the EETX estimator
// called when new beacon estimate is done
// also called when new DEETX estimate is done
void LinkEstimator::updateEETX(neighbor_table_entry_t *ne, uint16_t newEst) {
	ne->eetx = (ALPHA * ne->eetx + (10 - ALPHA) * newEst)/10;
}

// update data driven EETX
void LinkEstimator::updateDEETX(neighbor_table_entry_t *ne) {
	uint16_t estETX;

	if (ne->data_success == 0) {
		// if there were no successful packet transmission in the
		// last window, our current estimate is the number of failed
		// transmissions
		estETX = (ne->data_total - 1)* 10;
	} else {
		estETX = (10 * ne->data_total) / ne->data_success - 10;
		ne->data_success = 0;
		ne->data_total = 0;
	}
	updateEETX(ne, estETX);
}

// EETX (Extra Expected number of Transmission)
// EETX = ETX - 1
// computeEETX returns EETX*10
uint8_t LinkEstimator::computeEETX(uint8_t q1) {
	uint16_t q;
	if (q1 > 0) {
		q =  2550 / q1 - 10;
		if (q > 255) {
			q = VERY_LARGE_EETX_VALUE;
		}
		return (uint8_t)q;
	} else {
		return VERY_LARGE_EETX_VALUE;
	}
}

// update the inbound link quality by
// munging receive, fail count since last update
void LinkEstimator::updateNeighborTableEst(am_addr_t n) {
	uint8_t i, totalPkt;
	neighbor_table_entry_t *ne;
	uint8_t newEst;
	uint8_t minPkt;

	minPkt = BLQ_PKT_WINDOW;
	trace()<<"updateNeibhgorTableEst" ;
	for (i = 0; i < NEIGHBOR_TABLE_SIZE; i++) {
		ne = &NeighborTable[i];
		if (ne->ll_addr == n) {
			if (ne->flags & VALID_ENTRY) {
				if (ne->inage > 0)
					ne->inage--;

				if (ne->inage == 0) {
					ne->flags ^= VALID_ENTRY;
					ne->inquality = 0;
				} else {
					trace()<<"Making link: "<<(int)i<<" mature";
					ne->flags |= MATURE_ENTRY;
					totalPkt = ne->rcvcnt + ne->failcnt;
					trace()<<"MinPkt: "<<(int)minPkt<<", totalPkt: "<<(int)totalPkt;
					if (totalPkt < minPkt) {
						totalPkt = minPkt;
					}
					if (totalPkt == 0) {
						ne->inquality = (ALPHA * ne->inquality) / 10;
					} else {
						newEst = (255 * ne->rcvcnt) / totalPkt;
						trace()<<(int)ne->ll_addr<<": "<<(int)ne->inquality<<" -> "<<(int)((ALPHA * ne->inquality + (10-ALPHA) * newEst)/10) ;
						ne->inquality = (ALPHA * ne->inquality + (10-ALPHA) * newEst)/10;
					}
					ne->rcvcnt = 0;
					ne->failcnt = 0;
				}
				updateEETX(ne, computeEETX(ne->inquality));
			}
			else {
				trace()<<"- entry "<<(int)i<<" is invalid" ;
			}
		}
	}
}

// we received seq from the neighbor in idx
// update the last seen seq, receive and fail count
// refresh the age
void LinkEstimator::updateNeighborEntryIdx(uint8_t idx, uint8_t seq) {
	uint8_t packetGap;

	if (NeighborTable[idx].flags & INIT_ENTRY) {
		trace()<<"Init entry update" ;
		NeighborTable[idx].lastseq = seq;
		NeighborTable[idx].flags &= ~INIT_ENTRY;
	}

	packetGap = seq - NeighborTable[idx].lastseq;
	trace()<<"updateNeighborEntryIdx: prevseq "<<(int)NeighborTable[idx].lastseq<<", curseq "<<(int)seq<<", gap "<<(int)packetGap ;
	NeighborTable[idx].lastseq = seq;
	NeighborTable[idx].rcvcnt++;
	NeighborTable[idx].inage = MAX_AGE;
	if (packetGap > 0) {
		NeighborTable[idx].failcnt += packetGap - 1;
	}
	if (packetGap > MAX_PKT_GAP) {
		NeighborTable[idx].failcnt = 0;
		NeighborTable[idx].rcvcnt = 1;
		NeighborTable[idx].inquality = 0;
	}

	if (NeighborTable[idx].rcvcnt >= BLQ_PKT_WINDOW) {
		updateNeighborTableEst(NeighborTable[idx].ll_addr);
	}

}

// print the neighbor table. for debugging.
void LinkEstimator::print_neighbor_table() {
	uint8_t i;
	neighbor_table_entry_t *ne;
	for (i = 0; i < NEIGHBOR_TABLE_SIZE; i++) {
		ne = &NeighborTable[i];
		if (ne->flags & VALID_ENTRY) {
			trace()<<(int)i<<":"<<(int)ne->ll_addr<<" inQ="<<(int)ne->inquality<<", inA="<<(int)ne->inage<<", rcv="<<(int)ne->rcvcnt<<", fail="<<(int)ne->failcnt<<", Q="<<(int)computeEETX(ne->inquality)  ;
		}
	}
}
//
//// print the packet. for debugging.
//void print_packet(message_t* msg, uint8_t len) {
//	uint8_t i;
//	uint8_t* b;
//
//	b = (uint8_t *)msg->data;
//	for(i=0; i<len; i++)
//		dbg_clear("LI", "%x ", b[i]);
//	dbg_clear("LI", "\n");
//}

// initialize the neighbor table in the very beginning
void LinkEstimator::initNeighborTable() {
	uint8_t i;

	for (i = 0; i < NEIGHBOR_TABLE_SIZE; i++) {
		NeighborTable[i].flags = 0;
	}
}

error_t LinkEstimator::command_StdControl_start() {
	Enter_Method("command_StdControl_start") ;
	trace()<<"Link estimator start";
	return SUCCESS;
}

error_t LinkEstimator::command_StdControl_stop() {
	Enter_Method("command_StdControl_stop") ;
	return SUCCESS;
}

/*
 * LinkEstimator Interface -------------------------------------------------------------
 */
// return bi-directional link quality to the neighbor
uint16_t LinkEstimator::command_LinkEstimator_getLinkQuality(am_addr_t neighbor) {
	Enter_Method("command_LinkEstimator_getLinkQuality") ;
	uint8_t idx;
	idx = findIdx(neighbor);
	if (idx == INVALID_RVAL) {
		return VERY_LARGE_EETX_VALUE;
	} else {
		if (NeighborTable[idx].flags & MATURE_ENTRY) {
			return NeighborTable[idx].eetx;
		} else {
			return VERY_LARGE_EETX_VALUE;
		}
	}
}

// insert the neighbor at any cost (if there is a room for it)
// even if eviction of a perfectly fine neighbor is called for
error_t LinkEstimator::command_LinkEstimator_insertNeighbor(am_addr_t neighbor) {
	Enter_Method("command_LinkEstimator_insertNeighbor") ;
	uint8_t nidx;

	nidx = findIdx(neighbor);
	if (nidx != INVALID_RVAL) {
		trace()<<"insert: Found the entry, no need to insert";
		return SUCCESS;
	}

	nidx = findEmptyNeighborIdx();
	if (nidx != INVALID_RVAL) {
		trace()<<"insert: inserted into the empty slot";
		initNeighborIdx(nidx, neighbor);
		return SUCCESS;
	} else {
		nidx = findWorstNeighborIdx(BEST_EETX);
		if (nidx != INVALID_RVAL) {
			trace()<<"insert: inserted by replacing an entry for neighbor: "<<(int)NeighborTable[nidx].ll_addr ;
			signal_LinkEstimator_evicted(NeighborTable[nidx].ll_addr) ;
			initNeighborIdx(nidx, neighbor);
			return SUCCESS;
		}
	}
	return FAIL;
}

// pin a neighbor so that it does not get evicted
error_t LinkEstimator::command_LinkEstimator_pinNeighbor(am_addr_t neighbor) {
	Enter_Method("command_LinkEstimator_pinNeighbor") ;
	uint8_t nidx = findIdx(neighbor);
	if (nidx == INVALID_RVAL) {
		return FAIL;
	}
	NeighborTable[nidx].flags |= PINNED_ENTRY;
	return SUCCESS;
}

// pin a neighbor so that it does not get evicted
error_t LinkEstimator::command_LinkEstimator_unpinNeighbor(am_addr_t neighbor) {
	Enter_Method("command_LinkEstimator_unpinNeighbor") ;
	uint8_t nidx = findIdx(neighbor);
	if (nidx == INVALID_RVAL) {
		return FAIL;
	}
	NeighborTable[nidx].flags &= ~PINNED_ENTRY;
	return SUCCESS;
}

// called when an acknowledgement is received; sign of a successful
// data transmission; to update forward link quality
error_t LinkEstimator::command_LinkEstimator_txAck(am_addr_t neighbor) {
	Enter_Method("command_LinkEstimator_txAck") ;
	neighbor_table_entry_t *ne;
	uint8_t nidx = findIdx(neighbor);
	if (nidx == INVALID_RVAL) {
		return FAIL;
	}
	ne = &NeighborTable[nidx];
	ne->data_success++;
	ne->data_total++;
	if (ne->data_total >= DLQ_PKT_WINDOW) {
		updateDEETX(ne);
	}
	return SUCCESS;
}

// called when an acknowledgement is not received; could be due to
// data pkt or acknowledgement loss; to update forward link quality
error_t LinkEstimator::command_LinkEstimator_txNoAck(am_addr_t neighbor) {
	Enter_Method("command_LinkEstimator_txNoAck");
	neighbor_table_entry_t *ne;
	uint8_t nidx = findIdx(neighbor);
	if (nidx == INVALID_RVAL) {
		return FAIL;
	}

	ne = &NeighborTable[nidx];
	ne->data_total++;
	if (ne->data_total >= DLQ_PKT_WINDOW) {
		updateDEETX(ne);
	}
	return SUCCESS;
}

// called when the parent changes; clear state about data-driven link quality
error_t LinkEstimator::command_LinkEstimator_clearDLQ(am_addr_t neighbor) {
	Enter_Method("command_LinkEstimator_clearDLQ") ;
	neighbor_table_entry_t *ne;
	uint8_t nidx = findIdx(neighbor);
	if (nidx == INVALID_RVAL) {
		return FAIL;
	}
	ne = &NeighborTable[nidx];
	ne->data_total = 0;
	ne->data_success = 0;
	return SUCCESS;
}
// -------------------------------------------------------------------------------------

// user of link estimator calls send here
// slap the header and footer before sending the message
error_t LinkEstimator::command_Send_send(am_addr_t addr, cPacket* pkt) {
	Enter_Method("command_Send_send") ;
	take(pkt) ; // required in omnet: I cannot send a packet if I'm not the owner.
	CtpLe* lePkt = new CtpLe() ; // initialize the LinkEstimator packet
	lePkt->setKind(NETWORK_LAYER_PACKET);
	lePkt->getNetMacInfoExchange().lastHop = self ; // standard routing packet fields
	uint8_t ovhd = addLinkEstHeaderAndFooter(lePkt,(uint8_t)pkt->getByteLength()); // add the header and dynamically adds the size of the footer. Note that actually there is no footer but just a bigger header.
	lePkt->setByteLength(ovhd) ;
	lePkt->encapsulate(pkt) ;

	trace()<<"Sending seq: "<<(int)linkEstSeq ;
	//	print_packet(msg, newlen);

	return db->command_Send_send(addr,lePkt) ; // the message is sent via DualBuffer. We don't need to keep a copy locally.
}

void LinkEstimator::event_Send_sendDone(cMessage* msg,error_t err){
	Enter_Method("event_SubSend_sendDone") ;
	signal_Send_sendDone(msg,err) ;
}

// These functions are useless in our implementation -> skipped
//// cascade the calls down
//command uint8_t Send.cancel(message_t* msg) {
//	return call AMSend.cancel(msg);
//}
//
//command uint8_t Send.maxPayloadLength() {
//	return call Packet.maxPayloadLength();
//}
//
//command void* Send.getPayload(message_t* msg, uint8_t len) {
//	return call Packet.getPayload(msg, len);
//}

// called when link estimator generator packet or
// packets from upper layer that are wired to pass through
// link estimator is received
void LinkEstimator::processReceivedMessage(CtpLe* msg) {
	uint8_t nidx;
	uint8_t num_entries;

	trace()<<"LI, receiving packet." ;
	//	print_packet(msg, len);

	if (command_SubAMPacket_destination(msg) == AM_BROADCAST_ADDR) {
		am_addr_t ll_addr;

		ll_addr = command_SubAMPacket_source(msg) ;

		trace()<<"Got seq: "<<(int)msg->getSeq()<<" from link: "<<(int)ll_addr;

		num_entries = msg->getFlags() & NUM_ENTRIES_FLAG ;

		print_neighbor_table();

		// update neighbor table with this information
		// find the neighbor
		// if found
		//   update the entry
		// else
		//   find an empty entry
		//   if found
		//     initialize the entry
		//   else
		//     find a bad neighbor to be evicted
		//     if found
		//       evict the neighbor and init the entry
		//     else
		//       we can not accommodate this neighbor in the table
		nidx = findIdx(ll_addr);
		if (nidx != INVALID_RVAL) {
			trace()<<"Found the entry so updating" ;
			updateNeighborEntryIdx(nidx, msg->getSeq());
		} else {
			nidx = findEmptyNeighborIdx();
			if (nidx != INVALID_RVAL) {
				trace()<<"Found an empty entry" ;
				initNeighborIdx(nidx, ll_addr);
				updateNeighborEntryIdx(nidx, msg->getSeq());
			} else {
				nidx = findWorstNeighborIdx(EVICT_EETX_THRESHOLD);
				if (nidx != INVALID_RVAL) {
					trace()<<"Evicted neighbor "<<(int)NeighborTable[nidx].ll_addr<<" at idx "<<(int)nidx ;
					signal_LinkEstimator_evicted(NeighborTable[nidx].ll_addr) ;
					initNeighborIdx(nidx, ll_addr);
				} else {
					trace()<<"No room in the table";
					cPacket* dupMsg = msg->dup() ;
					if (signal_CompareBit_shouldInsert(dupMsg->decapsulate(),command_LinkPacketMetadata_highChannelQuality(msg))) {
						nidx = findRandomNeighborIdx();
						if (nidx != INVALID_RVAL) {
							signal_LinkEstimator_evicted(NeighborTable[nidx].ll_addr) ;
							initNeighborIdx(nidx, ll_addr);
						}
					}
					delete dupMsg ;
				}
			}
		}
	}
}

// new messages are received here
// update the neighbor table with the header
// and footer in the message
// then signal the user of this component
void LinkEstimator::event_SubReceive_receive(CtpLe* msg) {
	trace()<<"Received upper packet. will signal up" ;
	processReceivedMessage(msg);
	cre->event_BeaconReceive_receive(msg->decapsulate()) ;
	delete msg ;
}

// The packet interface is useless in our implementation.

//command void Packet.clear(message_t* msg) {
//	call SubPacket.clear(msg);
//}
//
//// subtract the space occupied by the link estimation
//// header and footer from the incoming payload size
//command uint8_t Packet.payloadLength(message_t* msg) {
//	linkest_header_t *hdr;
//	hdr = getHeader(msg);
//	return call SubPacket.payloadLength(msg)
//    		  - sizeof(linkest_header_t)
//    		  - sizeof(linkest_footer_t)*(NUM_ENTRIES_FLAG & hdr->flags);
//}
//
//// account for the space used by header and footer
//// while setting the payload length
//command void Packet.setPayloadLength(message_t* msg, uint8_t len) {
//	linkest_header_t *hdr;
//	hdr = getHeader(msg);
//	call SubPacket.setPayloadLength(msg,
//			len
//			+ sizeof(linkest_header_t)
//			+ sizeof(linkest_footer_t)*(NUM_ENTRIES_FLAG & hdr->flags));
//}
//
//command uint8_t Packet.maxPayloadLength() {
//	return call SubPacket.maxPayloadLength() - sizeof(linkest_header_t);
//}
//
//// application payload pointer is just past the link estimation header
//command void* Packet.getPayload(message_t* msg, uint8_t len) {
//	void* payload = call SubPacket.getPayload(msg, len + sizeof(linkest_header_t));
//	if (payload != NULL) {
//		payload += sizeof(linkest_header_t);
//	}
//	return payload;
//}

////////////////// Custom Functions //////////////////////////
//////////////////////////////////////////////////////////////

void LinkEstimator::signal_LinkEstimator_evicted(am_addr_t n){
	cre->event_LinkEstimator_evicted(n) ;
}

void LinkEstimator::signal_Send_sendDone(cMessage* msg,error_t err){
	cre->event_BeaconSend_sendDone(msg, err);
}

bool LinkEstimator::signal_CompareBit_shouldInsert(cPacket* pkt, bool white_bit){
	return cre->event_CompareBit_shouldInsert(pkt,white_bit) ;
}

am_addr_t LinkEstimator::command_SubAMPacket_destination(cPacket* msg){
	RoutingPacket* pkt = check_and_cast<RoutingPacket*>(msg) ;
	return pkt->getNetMacInfoExchange().nextHop ;
}

am_addr_t LinkEstimator::command_SubAMPacket_source(cPacket* msg){
	RoutingPacket* pkt = check_and_cast<RoutingPacket*>(msg) ;
	return pkt->getNetMacInfoExchange().lastHop ;
}

/*
 * The lqi field of the CC2420 packet is derived from the correlation value
 * represented by the 7 less significant bits of the last FCS byte (fig. 20 of CC2420 datasheet).
 * Here I use the lqi field of castalia, but don't know if it's exactly the same...
 * In any case this value is not used in the actual implementation of CTP for TinyOs 2.1 .
 * Further check is needed.
 */
bool LinkEstimator::command_LinkPacketMetadata_highChannelQuality(cPacket* msg) {
	RoutingPacket* pkt = check_and_cast<RoutingPacket*>(msg) ;
	return (pkt->getNetMacInfoExchange().LQI > 105.0) ;
}

//////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////
