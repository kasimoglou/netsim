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

#ifndef _LINKESTIMATOR_H_
#define _LINKESTIMATOR_H_

#include "Ctp.h"

using namespace std;

/////////////////////////// LinkEstimator.h ////////////////////////////
////////////////////////////////////////////////////////////////////////

// the NEIGHBOR_TABLE_SIZE = 10 has been removed since it is defined through omnetpp.ini

// Masks for the flag field in the link estimation header
enum {
	// use last four bits to keep track of
	// how many footer entries there are
	NUM_ENTRIES_FLAG = 15,
};

// link estimator header added to
// every message passing through the link estimator
// linkest_header_t removed: fields are accessible through cPacket methods.

// neighbor_stat_entry has been moved in the CtpNoePackets.msg packet definition. Consequently, also the linkest_footer is useless.

// for outgoing link estimator message
// so that we can compute bi-directional quality
//typedef struct neighbor_stat_entry {
//  am_addr_t ll_addr;
//  uint8_t inquality;
//} neighbor_stat_entry_t;

// we put the above neighbor entry in the footer
//typedef struct linkest_footer {
//  neighbor_stat_entry_t neighborList[1];
//} linkest_footer_t;

// Flags for the neighbor table entry
enum {
	VALID_ENTRY = 0x1,
	// A link becomes mature after BLQ_PKT_WINDOW
	// packets are received and an estimate is computed
	MATURE_ENTRY = 0x2,
	// Flag to indicate that this link has received the
	// first sequence number
	INIT_ENTRY = 0x4,
	// The upper layer has requested that this link be pinned
	// Useful if we don't want to lose the root from the table
	PINNED_ENTRY = 0x8
};

// neighbor table entry
typedef struct neighbor_table_entry {
	// link layer address of the neighbor
	am_addr_t ll_addr;
	// last beacon sequence number received from this neighbor
	uint8_t lastseq;
	// number of beacons received after last beacon estimator update
	// the update happens every BLQ_PKT_WINDOW beacon packets
	uint8_t rcvcnt;
	// number of beacon packets missed after last beacon estimator update
	uint8_t failcnt;
	// flags to describe the state of this entry
	uint8_t flags;
	// MAXAGE-inage gives the number of update rounds we haven't been able
	// update the inbound beacon estimator
	uint8_t inage;
	// inbound qualities in the range [1..255]
	// 1 bad, 255 good
	uint8_t inquality;
	// EETX for the link to this neighbor. This is the quality returned to
	// the users of the link estimator
	uint16_t eetx;
	// Number of data packets successfully sent (ack'd) to this neighbor
	// since the last data estimator update round. This update happens
	// every DLQ_PKT_WINDOW data packets
	uint8_t data_success;
	// The total number of data packets transmission attempt to this neighbor
	// since the last data estimator update round.
	uint8_t data_total;
} neighbor_table_entry_t;

////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////

/////////////////////////// LinkEstimatorP.nc //////////////////////////
////////////////////////////////////////////////////////////////////////

// configure the link estimator and some constants
enum {
	// If the eetx estimate is below this threshold
	// do not evict a link
	EVICT_EETX_THRESHOLD = 55,
	// maximum link update rounds before we expire the link
	MAX_AGE = 6,
	// if received sequence number if larger than the last sequence
	// number by this gap, we reinitialize the link
	MAX_PKT_GAP = 10,
	BEST_EETX = 0,
	INVALID_RVAL = 0xff,
	INVALID_NEIGHBOR_ADDR = 0xff,
	// if we don't know the link quality, we need to return a value so
	// large that it will not be used to form paths
	VERY_LARGE_EETX_VALUE = 0xff,
	// decay the link estimate using this alpha
	// we use a denominator of 10, so this corresponds to 0.2
	ALPHA = 9,
	// number of packets to wait before computing a new
	// DLQ (Data-driven Link Quality)
	DLQ_PKT_WINDOW = 5,
	// number of beacons to wait before computing a new
	// BLQ (Beacon-driven Link Quality)
	BLQ_PKT_WINDOW = 3,
	// largest EETX value that we feed into the link quality EWMA
	// a value of 60 corresponds to having to make six transmissions
	// to successfully receive one acknowledgement
	LARGE_EETX_VALUE = 60
};

////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////


class DualBuffer ;
class CtpRoutingEngine ;
class LinkEstimator: public CastaliaModule , public TimerService{
 protected:

	/////////////////////////// LinkEstimatorP.nc //////////////////////////
	////////////////////////////////////////////////////////////////////////

	// keep information about links from the neighbors
	neighbor_table_entry_t* NeighborTable ;
	// link estimation sequence, increment every time a beacon is sent
	uint8_t linkEstSeq;
	// if there is not enough room in the packet to put all the neighbor table
	// entries, in order to do round robin we need to remember which entry
	// we sent in the last beacon
	uint8_t prevSentIdx;

	////////////////////////////////////////////////////////////////////////
	////////////////////////////////////////////////////////////////////////

	/////////////////////////// Custom Variables ///////////////////////////
	////////////////////////////////////////////////////////////////////////

	// Pointers to other modules.
	DualBuffer* db ;
	CtpRoutingEngine* cre ;

	// Node id
	int self;

	// LinkEstimator header overhead
	int ctpLeHeaderSize ;

	// neighborTableSize initialized with omnetpp.ini value (default 10 entries)
	int NEIGHBOR_TABLE_SIZE ;

	////////////////////////////////////////////////////////////////////////
	////////////////////////////////////////////////////////////////////////

	///////////// Castalia Functions /////////////////////////////////
	//////////////////////////////////////////////////////////////////

	virtual void initialize() ;
	virtual void handleMessage(cMessage * msg);
	virtual ~LinkEstimator() ;

	//////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////

	//////////////////// LinkEstimator functions //////////////////////
	///////////////////////////////////////////////////////////////////

	uint8_t addLinkEstHeaderAndFooter(CtpLe *msg,uint8_t len);
	void initNeighborIdx(uint8_t i, am_addr_t ll_addr) ;
	uint8_t findIdx(am_addr_t ll_addr) ;
	uint8_t findEmptyNeighborIdx() ;
	uint8_t findWorstNeighborIdx(uint8_t thresholdEETX) ;
	uint8_t findRandomNeighborIdx() ;
	void updateEETX(neighbor_table_entry_t *ne, uint16_t newEst);
	void updateDEETX(neighbor_table_entry_t *ne) ;
	uint8_t computeEETX(uint8_t q1) ;
	void updateNeighborTableEst(am_addr_t n) ;
	void updateNeighborEntryIdx(uint8_t idx, uint8_t seq) ;
	void print_neighbor_table() ;
	void initNeighborTable() ;

	void processReceivedMessage(CtpLe* msg) ;
	void event_SubReceive_receive(CtpLe* pkt) ;

	//////////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////////

	///////////////////////// Custom Functions ///////////////////////////
	//////////////////////////////////////////////////////////////////////

	void signal_LinkEstimator_evicted(am_addr_t n) ;
	void signal_Send_sendDone(cMessage* msg,error_t err);
	bool signal_CompareBit_shouldInsert(cPacket* pkt, bool white_bit) ;

	am_addr_t command_SubAMPacket_destination(cPacket* msg);
	am_addr_t command_SubAMPacket_source(cPacket* msg) ;

	bool command_LinkPacketMetadata_highChannelQuality(cPacket* msg) ;

	//////////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////////

 public:

	//////////////////// LinkEstimator functions //////////////////////
	///////////////////////////////////////////////////////////////////

	error_t command_StdControl_start() ;
	error_t command_StdControl_stop() ;

	// LinkEstimator Interface ----------------------------------------
	uint16_t command_LinkEstimator_getLinkQuality(uint16_t n) ;
	error_t command_LinkEstimator_insertNeighbor(am_addr_t n) ;
	error_t command_LinkEstimator_pinNeighbor(am_addr_t n) ;
	error_t command_LinkEstimator_unpinNeighbor(am_addr_t n) ;
	error_t command_LinkEstimator_txAck(am_addr_t dest) ;
	error_t command_LinkEstimator_txNoAck(am_addr_t dest) ;
	error_t command_LinkEstimator_clearDLQ(am_addr_t n) ;
	// ----------------------------------------------------------------

	error_t command_Send_send(am_addr_t addr, cPacket* pkt) ;
	void event_Send_sendDone(cMessage* msg,error_t err) ;

	///////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////

};
#endif
