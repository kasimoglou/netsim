'''
Created on Mar 2, 2014

@author: vsam
'''



import multiprocessing as mp

import argparse 
import logging
import runner.DAO as DAO
import os.path, sys, signal
import runner.guiapp as guiapp

from runner.config import *
from runner.monitor import Manager
from setup_castalia import assertCastaliaSetup, assertFileExists
from runner.dpcmrepo import initialize_repo


def daemon_init(logfile = None):
    nullfd = os.open("/dev/null",os.O_RDWR)
    if logfile:
        logfd = logfile.fileno()
    else:
        logfd = nullfd

    # fork, parent exits
    if os.fork()!=0: os._exit(0)

    # become session leader
    os.setsid()

    # ignore SIGHUP and fork again, parent dies
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    if os.fork()!=0: os._exit(0)

    # setup a clean slate
    os.umask(0)
    os.chdir('/')

    # reset standard I/O
    os.dup2(nullfd,0)
    os.dup2(logfd,1)
    os.dup2(logfd,2)

    
#
# from http://www.electricmonk.nl
#
class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''
    
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

def start(args):

    # configure logging
    config_log(args)    
    logging.info("WSN-DPCM Network Simulation Execution Monitor")


    # Read configuration file
    configure('sim_runner', args.config)


    # daemonize if needed
    if args.daemon:
        daemon_init()
        # redirect Python's standard streams to the log     
        stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl
         
        stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl
        
        print("In Stdout: this is my PID:", os.getpid())
        logging.critical("My Pid= %s", os.getpid())   

    # Does this have to go higher?
    mp.set_start_method('forkserver')


    # check Castalia configuration
    try:
        assertCastaliaSetup()
        # also check that setup_castalia has been run
        assertFileExists(castalia_path(), "makefrag.inc")
    except AssertionError:
        logging.exception("Checking castalia setup")
        logging.critical("Cannot execute simulations. Exiting.")
        return

    
    # check database configuration
    DAO.check_database(args, postgresql_connection())
    logging.info("Verified database configuration")

    # check gui file location
    if not os.access(os.path.join(gui_file_path(), "mainpage.html"), os.R_OK):
        logging.critical("Cannot find the GUI files in location %s",gui_file_path())
        os._exit(1)
    logging.info("Gui files located")

    # initialize project repository
    initialize_repo()


    #
    # ok, enough checks, now we go ahead with the boot
    #
    
    # Augment for Omnet++
    augmentEnvironment()
    logging.info("Set up envorinemt vars for OmNet++")
    
    # boot the monitors
    try:
        Manager.initialize(postgresql_connection())
    except Exception as e:
        logging.critical("Failed to initialize Manager")
        logging.exception("Exception from Manager.initialize")
        os._exit(1)
    
    logging.info("Starting gui")
    guiapp.start_gui(args, gui_bind_address())


    logging.info("Starting shutdown")
    Manager.shutdown()    
    logging.warning("Shutdown complete")
    


def config_log(args):
    
    level = {'DEBUG': logging.DEBUG,
             'INFO' : logging.INFO,
             'WARN' : logging.WARN,
             'ERROR' : logging.ERROR,
             'CRITICAL' : logging.CRITICAL
             }[args.ll]
    
    print('Logging level',level, ' file=',args.log)
    if not args.daemon:
        args.log = None
    if args.log is not None:
        from logging import Formatter
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(args.log)
        handler.setLevel(level)
        formatter = Formatter(fmt="[%(asctime)s] %(levelname)s:%(name)s:%(message)s")
        handler.setFormatter(formatter)
        logging.root.addHandler(handler)
    logging.root.setLevel(level)
    logging.critical("Logging configured. Level=%s(%d), logfile=%s", args.ll, level, args.log)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--log',help="specify the log filename", default="simrunner.log")
    parser.add_argument('--ll',help="specify the log level",
                        default='WARN', choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    parser.add_argument('--initdb',help="specify whether the database is to be recreated",
                        default='NO', choices=['NO','IFNEEDED','YES'])
    parser.add_argument('--daemon', help="become a daemon (implies logging to a file)",
                            action="store_true")
    parser.add_argument('--config', help="Path to configuration file (defaults to %s)" % DEFAULT_CFGFILE,
                            default=None)
    args = parser.parse_args()

    start(args)
