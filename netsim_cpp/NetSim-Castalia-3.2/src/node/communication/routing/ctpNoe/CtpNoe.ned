// /*
//  * @author Ugo Colesanti
//  * @author Silvia Santini
//  * @version 1.0 (January 27, 2011)
//  *
//  * Acknowledgment: This code is based upon the implementation of CTP for TinyOS written by
//  * Omprakash Gnawali, Philip Levis, Kyle Jamieson, and Rodrigo Fonseca.
//  */

// /*
//  * Copyright (c) 2011 Sapienza University of Rome.
//  * All rights reserved.
//  *
//  * Redistribution and use in source and binary forms, with or without
//  * modification, are permitted provided that the following conditions
//  * are met:
//  * - Redistributions of source code must retain the above copyright
//  *   notice, this list of conditions and the following disclaimer.
//  * - Redistributions in binary form must reproduce the above copyright
//  *   notice, this list of conditions and the following disclaimer in the
//  *   documentation and/or other materials provided with the
//  *   distribution.
//  * - Neither the name of the Sapienza University of Rome nor the names of
//  *   its contributors may be used to endorse or promote products derived
//  *   from this software without specific prior written permission.
//  *
//  * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
//  * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
//  * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
//  * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL SAPIENZA 
//  * UNIVERSITY OF ROME OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
//  * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
//  * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
//  * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
//  * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
//  * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
//  * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
//  * OF THE POSSIBILITY OF SUCH DAMAGE.
//  */
 
// /*
//  * Copyright (c) 2011 ETH Zurich.
//  * All rights reserved.
//  *
//  * Redistribution and use in source and binary forms, with or without
//  * modification, are permitted provided that the following conditions
//  * are met:
//  * - Redistributions of source code must retain the above copyright
//  *   notice, this list of conditions and the following disclaimer.
//  * - Redistributions in binary form must reproduce the above copyright
//  *   notice, this list of conditions and the following disclaimer in the
//  *   documentation and/or other materials provided with the
//  *   distribution.
//  * - Neither the name of ETH Zurich nor the names of
//  *   its contributors may be used to endorse or promote products derived
//  *   from this software without specific prior written permission.
//  *
//  * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
//  * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
//  * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
//  * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL ETH 
//  * ZURICH OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
//  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
//  * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
//  * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
//  * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
//  * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
//  * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
//  * OF THE POSSIBILITY OF SUCH DAMAGE.
//  */
 
package node.communication.routing.ctpNoe;

module CtpNoe like node.communication.routing.iRouting
{
	parameters:
		bool collectTraceInfo = default (false);
		int maxNetFrameSize = default (0);	// bytes
		int netDataFrameOverhead = default (10);	// bytes
		int netBufferSize = default (32);	// number of messages
	
	gates:
		output toCommunicationModule;
		output toMacModule;
		input fromCommunicationModule;
		input fromMacModule;
		input fromCommModuleResourceMgr;
		
	submodules:
		Ctp: node.communication.routing.ctpNoe.components.Ctp ;
		CtpForwardingEngine: node.communication.routing.ctpNoe.components.CtpForwardingEngine ;
		CtpRoutingEngine: node.communication.routing.ctpNoe.components.CtpRoutingEngine ;
		LinkEstimator: node.communication.routing.ctpNoe.components.LinkEstimator ;
		DualBuffer: node.communication.routing.ctpNoe.components.DualBuffer ;
	
	connections:
		fromCommunicationModule --> Ctp.fromCommunicationModule ;
		fromMacModule --> Ctp.fromMacModule ;
		fromCommModuleResourceMgr --> Ctp.fromCommModuleResourceMgr ;
		Ctp.toMacModule --> toMacModule ;
		Ctp.toCommunicationModule --> toCommunicationModule ;
		Ctp.toCtpForwardingEngine --> CtpForwardingEngine.fromCtp ;
		Ctp.toCtpRoutingEngine --> CtpRoutingEngine.fromCtp ;
		Ctp.toLinkEstimator --> LinkEstimator.fromCtp ;
		Ctp.toDualBuffer --> DualBuffer.fromCtp ;
		CtpForwardingEngine.toCtp --> Ctp.fromCtpForwardingEngine ;
		CtpRoutingEngine.toCtp --> Ctp.fromCtpRoutingEngine ;
		LinkEstimator.toCtp --> Ctp.fromLinkEstimator ;
		DualBuffer.toCtp --> Ctp.fromDualBuffer ;
}