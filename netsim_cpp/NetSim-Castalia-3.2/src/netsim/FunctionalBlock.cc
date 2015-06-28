
#include "FunctionalBlock.h"



FunctionalBlock::FunctionalBlock() : cSimpleModule(65536), _OpSys(0) { }


void FunctionalBlock::initialize()
{
	// Get the Os from the parent
	cModule* parent = getParentModule();
	this->_OpSys = check_and_cast<GenericOS*>(parent->getSubmodule("Os"));

	cerr << "Initialized module " << _OpSys->getName() << endl;
}

