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
//  * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL SAPIENZA 
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
//  * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ETH 
//  * ZURICH OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
//  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
//  * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
//  * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
//  * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
//  * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
//  * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
//  * OF THE POSSIBILITY OF SUCH DAMAGE.
//  */


// /*
//  * Copyright (c) 2006 Stanford University.
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
//  * - Neither the name of the Stanford University nor the names of
//  *   its contributors may be used to endorse or promote products derived
//  *   from this software without specific prior written permission.
//  *
//  * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
//  * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
//  * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
//  * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL STANFORD
//  * UNIVERSITY OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
//  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
//  * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
//  * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
//  * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
//  * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
//  * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
//  * OF THE POSSIBILITY OF SUCH DAMAGE.
//  */
 
cplusplus {{
#include "RoutingPacket_m.h"
}}

enum Notification_type ;
enum Notification_interface ;
enum Notification_command ;
enum Notification_event ;
enum tos_err_types ;

class RoutingPacket;

struct neighbor_stat_entry{
	uint16_t ll_addr;
	uint8_t inquality ;
};

packet CtpData extends RoutingPacket{
	uint8_t options ;
	uint8_t thl ;
	uint16_t etx ;
	uint16_t origin ;
	uint8_t originSeqNo ;
	uint8_t type ;
}

packet CtpBeacon extends RoutingPacket{
	uint8_t options ;
	uint16_t parent ;
	uint16_t etx ;
}

packet CtpLe extends CtpBeacon{
	uint8_t flags ;
	uint8_t seq ;
	neighbor_stat_entry linkest_footer[] ;
}

message CtpNotification{
	int cnType enum (Notification_type) ;
	int cnInterface enum (Notification_interface) ;
	int cnEvent enum (Notification_event) ;
	int cnCommand enum (Notification_command) ;
	uint8_t error enum (tos_err_types) ;
}