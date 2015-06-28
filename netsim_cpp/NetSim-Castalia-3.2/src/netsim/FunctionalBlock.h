#ifndef _GENERIC_OS_H_
#define _GENERIC_OS_H_

#include <typeinfo>
#include <string>
#include <boost/format.hpp>

#include "CastaliaModule.h"
#include "GenericOS.h"
#include "ApplicationPacket_m.h"

using namespace std;




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

};

#endif

