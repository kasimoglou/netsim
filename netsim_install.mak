#----------------------------------------------------------------------------
#
#  netsim_install  v1.0
#
#  This file is the installation script for WSN-DPCM Network Simulator.
#
#  Please make sure to go through the variables below and edit them to suit 
#  your needs.
#
#  
#
#  Release notes:
#  15/6/2015	This script has been tested on ubuntu server 14.04.2 LTS
#               but it should work on any newer variant as well
#----------------------------------------------------------------------------

#-----------------------------------
# Python3 executable
#-----------------------------------

PYTHON=python3


#-----------------------------------
# Installation directories
#-----------------------------------

# The location where the simulation homes will reside
ifndef INSTALL_DIR
INSTALL_DIR = $(PWD)
endif

# The path to the netsim source
NETSIM_DIR=$(PWD)/netsim



#---------------------------------------------------------------
# External dependencies
#
# These are the source distributions for OmNeT++ and Castalia
#----------------------------------------------------------------

OMNETPP_SRC_FILE= $(INSTALL_DIR)/omnetpp-4.4-src.tgz
CASTALIA_SRC_FILE= $(INSTALL_DIR)/Castalia-3.2.tar.gz






#----------------------------------------------------------------
#  Installation logic
#----------------------------------------------------------------

.PHONY: all check install

all: check install

#--------------------------------------------
#
#  Check the installation environment
#
#--------------------------------------------

.PHONY: check_external_files check_python3 check_gcc_cpp check_install_dir check_dbconn
check: check_install_dir check_external_files check_python3 check_gcc_cpp check_dbconn
	@echo "Everything seems in order."

.PRECIOUS: $(OMNET_SRC_FILE) $(CASTALIA_SRC_FILE)

$(OMNETPP_SRC_FILE):
	@echo "ERROR: Could not find Omnet++ source file:"  $(OMNETPP_SRC_FILE)
	@echo "Please edit the file netsim/netsim_install.mak to designate the correct path to the file."
	@false

$(CASTALIA_SRC_FILE):
	@echo "ERROR: Could not find Omnet++ source file:"  $(CASTALIA_SRC_FILE)
	@echo "Please edit the file netsim/netsim_install.mak to designate the correct path to the file."
	@false

check_install_dir:
	@echo "Installation directory:" $(INSTALL_DIR)

check_external_files:  $(OMNETPP_SRC_FILE) $(CASTALIA_SRC_FILE)
	@echo "Checking OmNet++ and Castalia files."


# Database connection needs to be provided at the command line
ifndef DBCONN
check_dbconn:
	@echo "ERROR: You need to specify a database connection string."
	@echo -e "For example,\n\n  % make DBCONN=\"dbase=dpcm\"\n\n"
	@echo "To form the database string, follow the syntax below".
	@$(PYTHON) $(NETSIM_SRC)/make_config.py -h
	@false
else
check_dbconn:
	@echo "Will use database at " $(DBCONN)
endif


.PHONY: check_python3
check_python3:
	@echo "Checking python environment."
	@$(PYTHON) netsim/check_python.py

check_gcc_cpp:
	@echo "Checking that g++ compiler is installed."
	@ (g++ --version > /dev/null) || (echo "GNU g++ not found! Please install a full GNU g++ compilation environment." && false)

#----------------------------------------
#
#  Installation
#
#----------------------------------------

.PHONY: install install_omnetpp install_config_file install_castalia executor

install: check install_omnetpp install_config_file install_castalia executor


NETSIM_PY= $(NETSIM_DIR)/netsim_py
NETSIM_SRC= $(NETSIM_PY)/src

OMNETPP_ROOT= $(INSTALL_DIR)/omnetpp-4.4
CASTALIA_ROOT= $(INSTALL_DIR)/Castalia-3.2

install_omnetpp: $(OMNETPP_ROOT)/bin/opp_run

# Restart omnetpp compilation from scratch
$(OMNETPP_ROOT)/bin/opp_run: $(OMNETPP_SRC_FILE)
	-rm -rf $(OMNETPP_ROOT)
	tar xzvf $(OMNETPP_SRC_FILE) -C $(INSTALL_DIR)
	cp netsim/omnet_cfg.user $(OMNETPP_ROOT)/configure.user
	@env PATH=$(PATH):$(OMNETPP_ROOT) LD_LIBRARY_PATH=$(OMNETPP_ROOT)/lib:$(LD_LIBRARY_PATH)  netsim/compile_omnetpp $(OMNETPP_ROOT)

install_config_file:  ~/.dpcm_netsim

~/.dpcm_netsim:
	$(PYTHON) netsim/netsim_py/src/make_config.py $(INSTALL_DIR) $(NETSIM_PY) $(DBCONN) > ~/.dpcm_netsim
	@echo "Configuration file created"


install_castalia: $(CASTALIA_ROOT)/libcastalia.so

$(CASTALIA_ROOT)/libcastalia.so: ~/.dpcm_netsim
	-rm -rf $(CASTALIA_ROOT)
	tar xvf $(CASTALIA_SRC_FILE) -C $(INSTALL_DIR)
	env PYTHONPATH=$(NETSIM_SRC)  $(PYTHON) -m setup_castalia

executor: $(INSTALL_DIR)/Simulations $(INSTALL_DIR)/src $(INSTALL_DIR)/Simulations/Parameters
	@echo "Created executor symlinks"

$(INSTALL_DIR)/Simulations:
	mkdir $(INSTALL_DIR)/Simulations

$(INSTALL_DIR)/src: $(CASTALIA_ROOT)/src
	ln -s -r $(CASTALIA_ROOT)/src $(INSTALL_DIR)/src

$(INSTALL_DIR)/Simulations/Parameters: $(CASTALIA_ROOT)/Simulations/Parameters
	ln -s -r $(CASTALIA_ROOT)/Simulations/Parameters $(INSTALL_DIR)/Simulations/Parameters

