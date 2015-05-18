'''
Created on Mar 4, 2014

@author: vsam
'''

import multiprocessing as mp
import os.path, errno, argparse, logging, sys, shutil, json

from runner.config import local_executor_path, configure
from runner.dpcmrepo import initialize_repo, repo
from runner.api import create_simoutput

from simgen.executor import LocalExecutor
from simgen.gen import Generator, register_generator
from simgen.tests.filestore import FileStore


class CopyGenerator(Generator):
    '''
    An implementation of Generator which copies files
    from another directory into the simulation home.
    
    This is only useful for testing.
    '''
    
    def __init__(self):
        super().__init__()


    @staticmethod
    def copy_files(src, dest):    
        if src!=dest:    
            cmd = "cp -a %s/* %s" % (src, dest)
            os.system(cmd)

    def generate(self):
        """Copy the contents of the datastore directory in the simhome.
        """
        assert isinstance(self.datastore, FileStore)
        self.log.info("Copying files from %s to %s", self.datastore.root_dir, self.simhome)
        self.copy_files(self.datastore.root_dir, self.simhome)
        
register_generator('CopyGenerator', CopyGenerator)


class StandaloneLocalExecutor(LocalExecutor):
    '''This executor is used by test code. It allows to determine the
    name of the simulation home.
    '''
    def __init__(self, name, homedir, fileloc):
        super().__init__(name, homedir, home_prefix = "run_")
        self.fileloc_base = fileloc

    def create_home_directory(self):
        '''
        Create and return a home directory (as an absolute path) for a new job.

        This method assures that a directory named by joining self.homedir 
        and self.fileloc_base exists and is empty. If the directory does not
        exist, it is created. If a file by this name does exist, it is erased and
        a directory is created. Finally, if the directory does exist, it is emptied.
        '''

        if self.fileloc_base is None:
            return LocalExecutor.create_home_directory(self)

        fileloc = os.path.join(self.homedir, self.fileloc_base)

        # Check if directory exists and clear it
        if not os.path.exists(fileloc):
            os.mkdir(fileloc)
        elif not os.path.isdir(fileloc):
            os.unlink(fileloc)
            os.mkdir(fileloc)

        assert os.path.isdir(fileloc)
        # We have a dir. Empty it...
        for fobj in os.listdir(fileloc):
            fobjpath = os.path.join(fileloc, fobj)
            if os.path.isdir(fobjpath): 
               shutil.rmtree(fobjpath)
            else:
                os.unlink(fobjpath)

        # create dir
        return fileloc


#-----------------------------------------------------
# the rest is just for testing
#-----------------------------------------------------

def simulation_run(executor, fileloc, redirect, stages):
    # test the run
    for stage in stages:
        if stage=='P':    
            executor.prepare_simulation(fileloc, redirect)
        elif stage=='G':    
            executor.generate_simulation(fileloc, redirect)
        elif stage=='C':    
            executor.compile_simulation(fileloc, redirect)
        elif stage=='S':    
            executor.start_simulation(fileloc, redirect)
        elif stage=='F':    
            executor.finish_simulation(fileloc, redirect)
        else:
            raise ValueError("stage unknown: {!r}".format(stage))
    
def copy_files(src, dest):    
    if src!=dest:    
        cmd = "cp -av %s/* %s" % (src, dest)
        os.system(cmd)

def create_simulation(xtor, args):
    '''This method will rewrite a uri, as described in the argument parser of
    main() and will create the simulation in the given executor xtor.

    Returns the path to the simulation home.
    '''
    
    if args.src.startswith('nsd:'):
        # Create simoutput
        nsdid = args.src[len('nsd:'):]
        initialize_repo(args.repo)
        prepo = repo()

        sim, url, simhome = create_simoutput(xtor, prepo, nsdid)
        return xtor.create_simulation(url, simhome)

    else:
        if any(args.src.startswith(p) 
            for p in ["http:", "file:"]):
            src = args.src
        else:
            src = 'file:'+os.path.abspath(args.src)
        return xtor.create_simulation(src)


    
def main():

    parser = argparse.ArgumentParser(description='''
    This program executes a simulation for the provided simulation object, or
    for a given NSD.

    It is possible to select a subset of the steps of a simulation. Also, the
    standard output of the execution is not redirected into files (unless -r is
    provided).

    The name of the simulation home can be provided.

    The program can be invoked as:
    % python3 simulation_run.py  [...options...]  <uri>
    where <uri> is:

    (a) file:/abs/path/to/sim.json   
        Then, the file /abs/path/to/sim.json must exist and contain a valid simoutput
        object. Furthermore, other files inside directory /abs/path/to  must exist, in order for the simulation to
        run smoothly. The resource directory contains such examples (e.g., see 
        directory  'netsim_py/resources/testsim1')

    (b) http://repo.site/dpcm_simulation/<simobj-id>
        The provided URL must point to a legal sim object, such as those created by

    (c) nsd:<nsdid>
        A new simoutput object is created on the configured project repository and
        a simulation is started on it.

    (d) If the uri starts with anything else, it is treated as a path. If needed,
        it is first converted to absolute and then 'file' is prepended to it.

    ''')
    parser.add_argument("src",  help="The uri of simulation.")
    
    parser.add_argument("--redir", '-r',
                        help=""""Redirect stdout and stdstream to files. If this option
                        is given, the execution will be quiet and standard stream files
                        will be created.""", 
                        default=False,
                        action="store_true")
    
    parser.add_argument("--loglevel", '-l',
                        help="Set the log level",
                        choices=['CRITICAL','ERROR','WARNING','INFO','DEBUG'],
                        default='DEBUG'
                        )

    parser.add_argument("--repo", '-p',
                        type=str,
                        help="""Give the url of a couchdb server to access as project
                        repository. If not provided, the default is used.""",
                        default = None)

    parser.add_argument("--name", '-n',
                        type=str,
                        help="""Set the simulation home name. If not set, a default 
                        name is provided.""")

    parser.add_argument("--stages", '-s',
                        help="""Define the stages to run. Stages are: P/G/C/S/F (Prepare/Generate/Compile/Start/Finish). 
                        For example -s PG means to only Prepare and Generate.""",
                        default="PGCSF")

    parser.add_argument("--config", help="Path to configuration file", default=None)
    args = parser.parse_args()

    assert args.loglevel is not None
    logging.root.setLevel(args.loglevel)

    mp.set_start_method("forkserver")

    logging.info("Logging level: %s", logging.getLevelName(logging.root.getEffectiveLevel()))
    logging.info("Redirect: %s",args.redir)
    
    configure('simulation_run', args.config)

    if not all(x in "PGCSF" for x in args.stages):
        logging.getLogger().error("Invalid stage sequence")
        sys.exit(1)

    # Create the simulation
    executor = StandaloneLocalExecutor('test', local_executor_path(), args.name)
    fileloc = create_simulation(executor, args)    
    print("Simulation home: ", fileloc)

    # Run the simulation
    simulation_run(executor, fileloc, args.redir, args.stages)
    
    print("Output: ", fileloc)


if __name__=='__main__':
    main()
    
