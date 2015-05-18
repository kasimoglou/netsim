'''
Main classes for simulation code generation.
Created on Sep 20, 2014

@author: vsam
'''


import logging
import os.path

from simgen.utils import put_file, get_file
from simgen.datastore import context
  


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
        self.log = logging.getLogger(os.path.basename(self.simhome))
        self.log.setLevel('DEBUG')
        
    
    def generate(self):
        '''
        Perform generation for the given simulation object.
        '''
        print("------------------------------------------------------------------GENERATION STARTED")
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



def generate_simulation(fileloc=None, loglevel='DEBUG'):
    """This function is called by the executor to bootstrap code generation.
    
    """

    # set logging level
    logging.getLogger().setLevel(loglevel)
    logging.info("Fetching root object")
    
    # Get the root object
    sim = context.datastore.get_root_object()

    # From the root object, select the proper Generator class
    GenCls = GENERATOR_REGISTRY[sim['generator']]
    generator = GenCls()
    generator.generate()

