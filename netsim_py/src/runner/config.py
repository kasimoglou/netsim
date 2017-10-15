'''
Created on Mar 3, 2014

Contains just configuration information

@author: vsam
@author: juls
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

    def getboolean(self, optname):
        '''
        Process and return the option as a boolean e..g, (yes/no), (1/0), etc
        recognized.
        '''
        return self.cfg.getboolean(self.section, optname)

    def defined(self, optname):
        'Return true if the given option name exists.'
        try:
            self.get(optname)
            return True
        except KeyError:
            return False

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

    # check for options
    fail = False
    for opt, detail in OPTIONS:
        if not cfg.defined(opt):
            logging.critical("Configuration file is missing required option '%s'\n   %s",opt, detail)
            fail = True
    if fail:
        raise RuntimeError("Incomplete configuration")

    for opt, detail in OPTIONS:
        logging.info("Configuration %25s : %s",opt, cfg[opt])

OPTIONS = [
    ('planning_tool_database', """The name of the PT database in the project repo."""),
    ('netsim_database', """The name of the network simulator database in the project repo."""),
    ('netsim_lib_database', """The name of the network simulator library database in the project repo."""),
    ('omnetpp_path',"""The path where OmNet++ is installed."""),
    ('castalia_path', """The path where Castalia is installed."""),
    ('hil_enabled', """Signals whether to attempt to execute HiL simulations, or ignore the indication."""),
    ('local_executor_path',"""The path where the local executor stores simulation homes."""),
    ('postgresql_connection', """The designation of the Postgresql connection, as expected by psycopg2."""),
    ('gui_bind_addr', """The host address to which the ReSTful services and the gui bind."""),
    ('gui_bind_port', """The port to which the ReSTful services and the gui bind"""),
    ('gui_file_path', """Path to the admin gui files."""),
    ('nsdEdit_file_path', """Path to the NSD editor gui files."""),
    ('http_server', """The name of http server. Use 'wsgiref' and 'cherrypy' for deployment."""),
    ('resource_path', """The path to resource files."""),
    ('project_repository', """The url to the project repository.""")
]



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
    

