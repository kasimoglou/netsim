'''
Executors are classes that contain the actual processing logic for all steps of
a generation.

Created on Sep 27, 2014

@author: vsam
'''

import logging
import os.path
import shutil
import tempfile
from simgen.utils import execute_command
from runner.config import castalia_path, omnetpp_path, augmentEnvironment
from simgen.datastore import set_root_url, context, execute_context
from simgen.gen import generate_simulation
from datavis.output_handler import generate_output


class Executor:
    '''
    Simulation executor.
    
    Instances of this class encapsulate the execution steps needed to
    carry out a simulation job execution.

    Each executor imposes limitations, depending on the
    nature of the executor, the versions of installed software etc.
    Instances contain sufficient metadata to drive generation as needed.
    
    In addition, this class offers an api via which the executor service can be accessed.
    '''
    
    def __init__(self, name, homedir, home_prefix = "sim_", **args):
        super().__init__()
        self.name = name
        self.homedir = homedir
        self.home_prefix = home_prefix
        self.log = logging.getLogger("%s[%s]" % (self.__class__.__name__, name))
        self.log.info("created")


    def create_simulation(self, url, simhome=None):
        '''
        This method creates and initializes a simulation.
        
        The default implementation:
        (a) if simhome is None, creates a simulation home directory
        by calling self.create_home_directory(), else checks the
        passed value to see that it is legal
        (c) stores the passed url, in textual format, into the file 
        'url.txt' inside simhome.
        '''
        if simhome is None:
            # create a new simhome
            try:
                simhome = self.create_home_directory()
            except:
                self.log.exception("Creating home directory for "+url)
                return None
        else:
            # check passed simhome to make sure it is legal
            if os.path.dirname(simhome)!=self.homedir:
                raise ValueError("Illegal simhome for this executor")
        # Now write url into file url.txt
        try:
            set_root_url(simhome, str(url))
        except:
            self.log.exception("Creating file url.txt")
            return None
        return simhome
    

    def create_home_directory(self):
        '''
        Return a home directory (as an absolute path) for a new job.
        This is where the code generator will place generated artifacts.
        '''
        return tempfile.mkdtemp(prefix=self.home_prefix, dir=self.homedir)


    def delete_simulation(self, job):
        '''
        Delete the home directory and all other state pertaining to this job.
        The job is already PASSIVE, so no execution is happening.
        '''
        try:
            shutil.rmtree(job.fileloc)
        except:
            logging.exception('Trying to delete directory %s',job.fileloc)


    #
    #  Abstract methods
    #
     
    
    def prepare_simulation(self, fileloc, redirect=True):
        raise NotImplementedError
   
    def generate_simulation(self, fileloc, redirect=True):
        raise NotImplementedError
    
    def compile_simulation(self, fileloc, redirect=True):
        raise NotImplementedError
        
    def start_simulation(self, fileloc, redirect=True):
        raise NotImplementedError

    def finish_simulation(self, fileloc, redirect=True):
        raise NotImplementedError
        
    def finalize(self, fileloc, jobid, jobstatus, redirect=True):
        raise NotImplementedError
        





class LocalExecutor(Executor):
    '''
    The direct executor service.
    
    These objects provide access to 'direct' engine types.
    '''


    def __init__(self, name, homedir, **args):
        '''
        Constructor.
        
        The direct executor performs job tasks on the same machine as the runner.
        
        name - a name for this executor
        homedir - the directory containing simulation homes.
        '''
        super().__init__(name, homedir, **args)
        augmentEnvironment()



    # The name for the final binary.
    SIMEXEC = "simexec"


    # easy linking to castalia directory
    @staticmethod
    def link_path(src, fileloc, dst):
        asrc = os.path.join(castalia_path(), src)
        adst = os.path.join(fileloc, dst)
        os.symlink(asrc, adst)


    @classmethod
    def make_opp_makemake_args(cls, fileloc):
        return [os.path.join(omnetpp_path(), "bin/opp_makemake"),
                "-f", "-r", "--deep", 
                "-o", cls.SIMEXEC, 
                "-u", "Cmdenv",
                "-P", fileloc,  ### Fileloc must be injected here
                "-M", "release",
                "-X./Simulations",
                "-X./src",
                "-L"+castalia_path(),
                "-lcastalia"]
 


    #-----------------------------------------------------
    # Prepare simulation
    #-----------------------------------------------------


     
    def prepare_simulation(self, fileloc, redirect=True):
        # we assume that fileloc is prepared correctly
        
        #
        # Perform various checks
        #
        
        # check that fileloc is an absolute path
        if not os.path.isabs(fileloc):
            raise RuntimeError("Path %s is not an absolute path" % (fileloc,))    
        
        if not os.path.isdir(fileloc):
            raise RuntimeError("Path %s is not a valid directory" % (fileloc,))
        
        # Not much to do here    
    
    #--------------------------------------------------------
    # Generate simulation
    #--------------------------------------------------------
    
    def generate_simulation(self, fileloc, redirect=True):
        # This will execute function generate_simulation() in a different process
        print("Fileloc:", fileloc)
        execute_context(fileloc, generate_simulation, "gen", redirect)
        print("Child id:::::::::::::::::::::::::::::", os.getpid())
        
    
    
    #--------------------------------------------------------
    # Compile simulation
    #--------------------------------------------------------
    
    
    def compile_simulation(self, fileloc, redirect=True):
    
        if not os.access(os.path.join(fileloc, "omnetpp.ini"), os.R_OK):
            raise RuntimeError("Cannot access omnetpp.ini at the root of path %s" % (fileloc,))
            
        #
        # Prepare the fileloc with additional files
        #
        
        # link files into fileloc
        self.link_path("makefrag.inc", fileloc, "makefrag")
        
        # Create the Makefile by executing opp_makemake 
        #
        args = self.make_opp_makemake_args(fileloc)
        execute_command(fileloc, args, "process", redirect)

        #
        # Build the simulation executable 
        #
        args = ["/usr/bin/make"]
        execute_command(fileloc, args, "compile", redirect)
    
    
    
    #--------------------------------------------------------
    # Compile simulation
    #--------------------------------------------------------
    
    
    def start_simulation(self, fileloc, redirect=True):
    
        #
        # Create the Makefile by executing opp_makemake 
        #
        prog = os.path.join(fileloc , self.SIMEXEC)
        args = [prog, '--cmdenv-output-file=simout.txt']
        execute_command(fileloc, args, "exec", redirect)
    
    
    #-----------------------------------------------------
    # Finish simulation
    #-----------------------------------------------------

    def finish_simulation(self, fileloc, redirect=True):
        #
        # Use the datavis module to produce and publish results
        #
        execute_context(fileloc, generate_output, "datavis", redirect)


        

    def finalize(self, fileloc, jobid, jobstatus, redirected=True):
        pass




_CLASSNAME_TO_CLASS = {
    'LocalExecutor': LocalExecutor
}
def instantiate_executor(name, className, home, args):
    """This is used to instantiate executors from a configuration.
    """
    cls = _CLASSNAME_TO_CLASS[className]
    return cls(name, home, **args) 
