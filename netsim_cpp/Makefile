###################################################
#
# Makefile for the libraries of dpcm netsim
#
# @author: vsam
#
###################################################

CXXFLAGS= -Wall -std=gnu++11

DEBUG=1

ifeq ($(DEBUG),1)
CXXFLAGS+= -g 
else
CXXFLAGS+= -O2 -DNDEBUG
endif

PROG_SRC = test1.cc
SRC = $(PROG_SRC)
OBJ = $(SRC:.cc=.o)
PROG = $(PROG_SRC:.cc=)

.PHONY: all

all: $(PROG)

test1: test1.o
	$(CXX) $(CXXFLAGS) -o $@ $+ 


clean:
	-rm *.o $(PROG)


depend:
	$(CXX) $(CXXFLAGS) -M *.cc > .depend

include .depend
