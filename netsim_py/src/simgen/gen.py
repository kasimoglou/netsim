'''
Main classes for simulation code generation.
Created on Sep 20, 2014

@author: vsam
'''


import logging
import os.path

from simgen.utils import put_file, get_file
from simgen.datastore import context, set_root_url
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

        retval = execute_function(fileloc, generate_simulation, 'val', redirect=True, raises=False)

        with open(os.path.join(fileloc, 'stdout.val.txt'), 'r') as f:
                retval['stdout'] = f.read()
        with open(os.path.join(fileloc, 'stderr.val.txt'), 'r') as f:
                retval['stderr'] = f.read()
    return retval


def generate_simulation(fileloc=None, loglevel=logging.DEBUG, raises=True):
    """
    This function is called by the executor to bootstrap code generation.
    """
    from models.validation import inform, warn

    print("loglevel=",loglevel)
    with GenProcess(loglevel) as genproc:
        # Get the root object
        sim = context.datastore.get_root_object()

        # From the root object, select the proper Generator class
        GenCls = GENERATOR_REGISTRY[sim['generator']]

        # run the generator
        try:
            generator = GenCls()
            generator.generate()
        except Exception as e:
            logger.exception("Mystery: %s", e, exc_info=1)
            logger.exception("Mystery:", exc_info=1)
            raise


    result = {
        'success': genproc.success,
        'messages': genproc.messages
    }


    print("Output messages:", len(genproc.messages))
    for msg in genproc.messages:
        print(msg['level'],':',msg['message'])

    if not genproc.success and raises:
        raise GenError(result)
    else:
        return result

