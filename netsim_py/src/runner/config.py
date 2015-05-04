'''
Created on Mar 3, 2014

Contains just configuration information

@author: vsam
'''

import os.path
import sys
import logging
from configparser import ConfigParser

#
# This is the version string
#
VERSION = "0.10"

#
# default location of configuration file.
#
DEFAULT_CFGFILE = "~/.dpcm_netsim"


class ConfigDict:
    '''
    A class used to store and access configuration options.

    It is initialized by function configure().
    '''

    def __init__(self):
        self.cfg = ConfigParser()
        self.section = 'DEFAULT'

    def read(self, sect, fnames):
        '''
        Read the configuration file 'fnames' and use section 'sect'
        to access options. If sect does not exist, default is used.
        '''
        self.cfg.read(fnames)
        self.section = sect

    def get(self, optname):
        '''Get configuration option.
            Raises KeyError if option does not exist.
        '''
        return self.cfg[self.section][optname]


    def __getattr__(self, optname):
        '''Get configuration option as an attribute, by calling self.get().
           Raises KeyError if option does not exist.
        '''
        return self.get(optname)

    def __getitem__(self, optname):
        '''Get configuration option as a key, by calling self.get().
           Raises KeyError if option does not exist.
        '''
        return self.get(optname)


cfg = ConfigDict()

#
# Configuration object
def configure(sect, cfgfile=None):
    '''
    Configure the global ConfigDict object.

    This function expands the user dir in cfgfile (which 
    defaults to ~/.dpcm_netsim), and then calls the
    read() method of the global ConfigDict.
    '''

    if cfgfile is None:
        cfgfile = DEFAULT_CFGFILE

    # read config file
    cfgf = os.path.expanduser(cfgfile)
    if not os.path.exists(cfgf):
        logging.critical("Cannot find configuration file")
        sys.exit("No configuration file")

    # check global var

    logging.info("Initialize configuration for %s", sect)
    cfg.read(sect, cfgf)


# 
# We assume that Omnet is built and works correctly. However, castalia 
# should not be built
#
# Tested with:
#    Omnet++   4.4
#   Castalia   3.2
def omnetpp_path():
    return cfg["omnetpp_path"]

def castalia_path():
    return cfg["castalia_path"]

#
#  We require a Postgres database (version >=8.0) that will be used by the monitor.
#
#  This is a minimal setup for Postgres. For more details consult the documentation
#  of psycopg2.
#
def postgresql_connection():
    return cfg["postgresql_connection"]


#
# Gui host and port
#
def gui_bind_address():
    return (cfg["gui_bind_addr"], int(cfg["gui_bind_port"]))    

#
# Location of the web templates
#

def gui_file_path():
    return cfg["gui_file_path"]

#
# Location of angular nsdEdit gui
#
def nsdEdit_file_path():
    assert cfg is not None
    return cfg["nsdEdit_file_path"]


#
# Path where the direct monitor jobs are to be stored
#

def local_executor_path():
    return cfg["local_executor_path"]


#
#Path where resource json files are stored
#

def resource_path():
    return cfg["resource_path"]


#
#CouchDb url's
#
def project_repository():
    return cfg["project_repository"]



#################################################
## DO NOT EDIT BELOW THIS LINE 
## UNLESS YOU KNOW WHAT YOU ARE DOING
#################################################


def executor_init():
    return [
    # name, class, path, extra args
    ('local', 'LocalExecutor', local_executor_path(), {})
    ]


def default_executor():
    return 'local'


def monitor_init():
    return [
    # name, number of workers
    ('main',  4)
    ]


#------------------------------------------
#  Set PATH and LD_LIBRARY_PATH for omnetpp
#------------------------------------------

import os

def augmentPath(evar, path):
    oldevar = os.getenv(evar,"")
    #check if exists
    if path not in oldevar.split(':'):
        os.environ[evar] = ':'.join((path, oldevar)) if oldevar else path


def augmentEnvironment():
    augmentPath("PATH", os.path.join(omnetpp_path(),"bin"))
    augmentPath("LD_LIBRARY_PATH", os.path.join(omnetpp_path(),"lib"))
    

