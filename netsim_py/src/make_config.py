"""
   This file is part of the configuration scripts of NetSim. It creates an initial
  configuration file for the standard layout of the netsim server.
"""


BASIC_TEMPLATE_1= \
"""
#
#  Generated configuration file for the WSN-DPCM network simulator
#
"""

BASIC_TEMPLATE_2 = \
"""
[DEFAULT]

# 
# The base paths for all the rest
#
execdir = %(execdir)s
netsim_py = %(netsim_py)s

#
#  We require a Postgres database (version >=8.0) that will be used by the monitor.
#
#  This is a minimal setup for Postgres. For more details consult the documentation
#  of psycopg2.
#
postgresql_connection: %(dbconn)s
"""

BASIC_TEMPLATE_3 = \
"""
#
# Paths to omnetpp and castalia 
#

omnetpp_path = %(execdir)s/omnetpp-4.4
castalia_path = %(execdir)s/Castalia-3.2

#
# Path where the direct monitor jobs are to be stored
#
local_executor_path= %(execdir)s/Simulations


planning_tool_database = dpcm_integration_repo
netsim_database = dpcm_simulator

#
# Gui host and port
#
gui_bind_addr=localhost
gui_bind_port=18880


#
# Location of the web templates
#
gui_file_path = %(netsim_py)s/src/runner/web
nsdEdit_file_path = %(netsim_py)s/src/runner/nsdEditor_gui

#
# Path where resource files are stored
#
resource_path= %(netsim_py)s/resources

#
# The http server to use
# 
; For developing
http_server = wsgiref
; For deployment
#http_server = cherrypy


#
# The url to the WSN-DPCM project repository
#
project_repository = http://213.172.45.30:5984/


# In this section you can customize defaults for the sim_runner server
[sim_runner]

# In this section you can customize defaults for the unit tests
[unit_test]

; The line below specifies a local couchdb Project Repo for running tests.
; 
; Using the setup_local_repo.py program, we can clone the DPCM
; Repository to the local couchdb

project_repository = http://127.0.0.1:5984/


# In this section you can customize defaults for simulation_run
[simulation_run]

"""


import argparse
import psycopg2

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='''This program will print a DPCM netsim configuration file to the standard output.''',
       formatter_class=argparse.RawDescriptionHelpFormatter,
       epilog="""\
This is the format for the database connection:

"""+psycopg2.connect.__doc__)

    parser.add_argument("execdir", help="The installation directory for the simulations.")
    parser.add_argument("netsim_py", help="The installation directory for the netsim source.")
    parser.add_argument("dbconn", help="The database connection string for netsim server.")  

    args = parser.parse_args()

    amap = {
        'execdir' : args.execdir,
        'netsim_py' : args.netsim_py,
        'dbconn' : args.dbconn
    }

    output = BASIC_TEMPLATE_1 + BASIC_TEMPLATE_2 % amap + BASIC_TEMPLATE_3

    print(output)
