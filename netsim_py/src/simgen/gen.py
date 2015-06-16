'''
Main classes for simulation code generation.
Created on Sep 20, 2014

@author: vsam
'''


import logging
import os.path
import tempfile


from simgen.utils import put_file, get_file, execute_function
from simgen.datastore import context, set_root_url, get_root_url, execute_context
from simgen.validation import GenProcess, GenError

logger = logging.getLogger('codegen')

class Generator:
    '''
    Simulation Generator base.
    
    This is an abstract base class for simulation generators.
    
    An instance of this class implements a generator.
    The code generator can customize the generation.
    Several kinds of generators may exist, depending on the 
    target executor.
    '''
    def __init__(self):
        super().__init__()
        self.simhome = context.fileloc
        self.sim_root = context.datastore.get_root_object()
        self.datastore = context.datastore
        self.sim_id = context.sim_id
        
    
    def generate(self):
        '''
        Perform generation for the given simulation object.
        '''
        raise NotImplementedError
    


from .castalia import CastaliaGen

class CastaliaGenerator(Generator, CastaliaGen):
    """The main class for the Castalia-based code generator.
    """

    def __init__(self):
        super().__init__()
        
    def generate(self):
        self.build_model()
        self.validate()
        self.generate_code()
    
    

GENERATOR_REGISTRY = {
    'Castalia': CastaliaGenerator
}

def register_generator(name, cls):
    GENERATOR_REGISTRY[name]=cls


def validate_simulation(nsd_url):
    '''
    Entry function for validating an nsd.
    '''
    with tempfile.TemporaryDirectory() as fileloc:
        # add the validation fragment
        url = nsd_url+"#validate"
        set_root_url(fileloc, url)

        logger.error("url=%s", get_root_url(fileloc))

        retval = execute_context(fileloc, generate_simulation, 'val', redir=True, 
            loglevel=logging.DEBUG, raises=False, validate=True)

        with open(os.path.join(fileloc, 'stdout.val.txt'), 'r') as f:
                retval['stdout'] = f.read()
        with open(os.path.join(fileloc, 'stderr.val.txt'), 'r') as f:
                retval['stderr'] = f.read()

    return retval


def generate_simulation(fileloc=None, loglevel=logging.DEBUG, raises=True, validate=False):
    """
    This function is called by the executor to bootstrap code generation.
    """
    from models.validation import inform, warn

    with GenProcess(loglevel) as genproc:
        # Get the root object
        try:
            context.validate = validate
            dstore = context.datastore
            sim = context.datastore.get_root_object()
        except Exception as e:
            logger.exception("In creating datastore", exc_info=1)
        inform("Created root object", sim)

        # From the root object, select the proper Generator class
        GenCls = GENERATOR_REGISTRY[sim['generator']]

        # run the generator
        generator = GenCls()
        generator.generate()


    result = {
        'success': genproc.success,
        'messages': genproc.messages,
        'nsd_id': sim['nsdid']
    }

    if not genproc.success and raises:
        raise GenError(result)
    else:
        return result

