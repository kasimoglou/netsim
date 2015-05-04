'''
Main classes for simulation code generation.



Created on Sep 20, 2014

@author: vsam
'''


import logging
import os.path

from simgen.utils import put_file, get_file
from simgen.datastore import get_root_url, create_datastore_proxy
  


class Generator:
    '''
    Simulation Generator base.
    
    This is an abstract base class for simulation generators.
    
    An instance of this class implements a generator.
    The code generator can customize the generation.
    Several kinds of generators may exist, depending on the 
    target executor.
    '''
    def __init__(self, simhome, sim_root, datastore):
        super().__init__()
        self.simhome = simhome
        self.sim_root = sim_root
        self.datastore = datastore
        self.log = logging.getLogger(os.path.basename(simhome))
            
    
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

    def __init__(self, simhome, sim_root, datastore):
        super().__init__(simhome, sim_root, datastore)
        
    def generate(self):
        self.build_model()
        self.validate()
        self.generate_code()
    
    

GENERATOR_REGISTRY = {
    'Castalia': CastaliaGenerator
}

def register_generator(name, cls):
    GENERATOR_REGISTRY[name]=cls



def generate_simulation(fileloc=None, loglevel='INFO'):
    """This function is called by the executor to bootstrap code generation.
    
    Its main function is to retrieve file 'url.txt' from directory 'fileloc',
    read its contents as a url, create the appropriate datastore and
    read the 'sim' (root) object
    """
    if fileloc is None:
        fileloc = os.getcwd()

    # set logging level
    logging.getLogger().setLevel(loglevel)
    logging.info("Fetching root object")
    
    # get the root url from url.txt    
    url = get_root_url(fileloc)
    with create_datastore_proxy(url) as datastore:
        # Get the root object
        sim = datastore.get_root_object()

        # From the root object, select the proper Generator class
        GenCls = GENERATOR_REGISTRY[sim['generator']]
        generator = GenCls(fileloc, sim, datastore)
        generator.generate()
"""       
def get_root_object_plan():

def get_root__object_project():            
"""
