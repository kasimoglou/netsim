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

#include "DualBuffer.h"
#include "CtpForwardingEngine.h"
#include "LinkEstimator.h"


Define_Module(DualBuffer);

/*
 * DUAL BUFFER MODULE
 * ------------------
 * The Dual Buffer Module receives packets from the ForwardingEngine and the LinkEstimator, it stores
 * them in memory (one packet per client) if room is available) and sends them as soon as possible in
 * a round robin fashion. The aim of the Dual Buffer Module is to replace the two instances of AMSender
 * used by the Collection Tree Protocol.
 *
 */

/*
 * Only one kind of cMessage is expected: the CC2420MacControlMessage that signals the sendDone (see technical
 * report for details).
 * Note that the packets to transmit are passed to this module through direct function calls so they are not managed
 * by this handleMessage function.
 */
void DualBuffer::handleMessage(cMessage * msg){
		int msgKind = msg->getKind();

		switch (msgKind) {
			case MAC_CONTROL_MESSAGE:{
				CC2420MacControlMessage* cc2420control = check_and_cast<CC2420MacControlMessage*>(msg) ;
				trace() << "ControlMessage, type: "<<cc2420control->getMcmType()<<", interface: "<<cc2420control->getMcmInterface()<<", c/e name: "<<cc2420control->getMcmEvent() ;
				if(cc2420control->getMcmType() == EVENT && cc2420control->getMcmInterface() == SEND && cc2420control->getMcmEvent() == EVT_SENDDONE){
					signal_send_sendDone(msg,cc2420control->getError()) ;
					sending = false ;
					tryToSend() ;
				}
				else if(cc2420control->getMcmType() == COMMAND_RETURN && cc2420control->getMcmInterface() == SEND && cc2420control->getMcmCommand() == CMD_SEND){
					trace()<<"Return value from send_send: "<<(int) cc2420control->getError() ;
					if(cc2420control->getError() != SUCCESS){
//						ostringstream os ;
//						os<<"Error returned: "<<(int) cc2420control->getError() ;
//						opp_error(os.str().c_str()) ;
						signal_send_sendDone(msg,cc2420control->getError()) ;
						sending = false ;
						tryToSend() ;
					}

				}
				else opp_error("Unexpected control message.") ;
				break ; // Delete the CC2420ControlMessage, DualBuffer is still the owner.
			}
			default:{
				opp_error("Unkown packet!") ;
			}

		}
		delete msg ;
};

void DualBuffer::initialize(){
	// Pointers to ForwardinfEngine and LinkEstimator modules.
	cfe = check_and_cast<CtpForwardingEngine*>(getParentModule()->getSubmodule("CtpForwardingEngine")) ;
	le = check_and_cast<LinkEstimator*>(getParentModule()->getSubmodule("LinkEstimator")) ;

	// lock flag for send.
	sending = false ;

	// stores the module to which the sendDone event must be signaled.
	justSentMsg = NONE ;
};

DualBuffer::~DualBuffer(){
	while(! dbuffer.empty()){
		delete dbuffer.pop() ;
	}
}

void DualBuffer::finishSpecific(){};


uint8_t DualBuffer::command_Send_send(uint16_t dest , cPacket* pkt){
	Enter_Method("command_send_send") ;
	take(pkt) ;// take the ownership of the packet (otherwise cannot send it)
	trace()<<"Send.Send() - buffering packet." ;
	RoutingPacket* msg = check_and_cast<RoutingPacket*>(pkt) ;
	msg->getNetMacInfoExchange().nextHop = dest ;

	/*
	 * 1) If buffer is empty -> no problem, store it and try to send.
	 *
	 * 2) If there is one room left -> check that the stored packet and incoming one are different (return EBUSY otherwise)
	 *
	 * 3) If there is no room -> return EBUSY
	 */


	if(sending){
		if((dynamic_cast<CtpData*>(pkt)!=NULL && justSentMsg==PACKET_FROM_FE)
				|| (dynamic_cast<CtpLe*>(pkt)!=NULL && justSentMsg==PACKET_FROM_LE)){
			return EBUSY ;
		}

	}

	if(dbuffer.empty()){
		dbuffer.insert(pkt) ;
		tryToSend() ;
	}
	else if(dbuffer.length() < 2 ){ //
		if((dynamic_cast<CtpData*>(pkt) != NULL && dynamic_cast<CtpData*>(dbuffer.front()) == NULL)||
		   (dynamic_cast<CtpLe*>(pkt) != NULL && dynamic_cast<CtpLe*>(dbuffer.front()) == NULL)){
			dbuffer.insert(pkt);
			tryToSend() ;
		}
		else{
			delete pkt ; // it's a copy, just delete it
			return EBUSY ;
		}
	}
	else{
		delete pkt ; // it's a copy, just delete it
		return EBUSY ;
	}
	return SUCCESS ;

}

void DualBuffer::signal_send_sendDone(cMessage* msg,uint8_t err){
	trace()<<"Signaling sendDone with err: "<<(int)err ;
	switch(justSentMsg){
		case PACKET_FROM_FE:{
			cfe->event_SubSend_sendDone(msg,err) ;
			break;
		}
		case PACKET_FROM_LE:{
			le->event_Send_sendDone(msg,err) ;
			break;
		}
		default:{
			opp_error("Unkown type!") ;
		}
	}
	justSentMsg = NONE ;

}

void DualBuffer::tryToSend(){
	if(!sending && dbuffer.length() > 0){
		sending = true ;

		cPacket* pkt = check_and_cast<cPacket*>(dbuffer.pop()) ;
		justSentMsg = (dynamic_cast<CtpLe*>(pkt) != NULL)? PACKET_FROM_LE:PACKET_FROM_FE ;
		RoutingPacket* msg = check_and_cast<RoutingPacket*>(pkt) ;
		trace()<<"Sending packet to "<<msg->getNetMacInfoExchange().nextHop;
		send(pkt,"toCtp") ;
	}
}
