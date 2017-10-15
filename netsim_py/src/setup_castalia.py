#! /usr/bin/python

'''
Created on Mar 2, 2014

@author: vsam
@author: juls
'''

import os, os.path

from runner.config import castalia_path, omnetpp_path, augmentEnvironment, configure


#-----------------------------------
# code to check the installation paths
#-----------------------------------
def assertFileExists(base, relfile):
    if not os.access( os.path.join(base, relfile), os.F_OK):
        message = "Directory %s is not legal " % base
        print(message)
        raise AssertionError(message)


def assertCastaliaSetup():
    assertFileExists(omnetpp_path(), "include/omnetpp.h")
    assertFileExists(castalia_path(), "bin/Castalia")
    



#------------------------------------------
#  Create shared library in Castalia
#------------------------------------------

# Safe and verbose execution for system
def echoExec(cmd):
    print(cmd)
    if os.system(cmd)!=0:
        raise SystemExit("Aborting, could not execute: "+cmd)

# Build a shared library from castalia sources
def buildCastaliaSharedLib():
    cmd = "opp_makemake -f -r --deep -s -o castalia -u Cmdenv -P %s -M release -X Simulations -X out -X bin" % castalia_path()
    os.chdir(castalia_path())
    echoExec(cmd)
    echoExec("make -j4")

# Create a makefile fragment with all include paths
def buildIncludePath():
    cmd = 'find '+castalia_path()+'/src -name "*.h" |xargs dirname |uniq|xargs printf "INCLUDE_PATH+= -I%s\n" > makefrag.inc'
    echoExec(cmd)


# server setup routine
def setupCastalia():
    assertCastaliaSetup()
    augmentEnvironment()
    
    print("Configuration: omnetpp  in %s" % omnetpp_path())
    print("Configuration: castalia in %s" % castalia_path())
    for evar in ("PATH","LD_LIBRARY_PATH"):
        print(evar,'=',os.getenv(evar))

    buildCastaliaSharedLib()
    buildIncludePath()
    
    
    print("Castalia has been set up successfully")
    

if __name__=='__main__':
    configure('sim_runner')
    setupCastalia()
