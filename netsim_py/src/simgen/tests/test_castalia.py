'''
Created on Oct 15, 2014

@author: vsam
'''



from simgen.castalia import CastaliaGen
from os.path import abspath, normpath, join, basename
from simgen.castalia import NSDReader
from simgen.datastore import create_datastore_proxy
from simgen.tests.filestore import FileStore


resource_path = normpath(abspath(join(basename(__file__), "../../resources")))



def test_reader_nsd_json():
    
    reader = NSDReader()
    
    datastore = create_datastore_proxy("file:"+join(resource_path, "testsim1/sim.json"))
    sim = datastore.get_root_object()
    
    nsd = reader.read_nsd(datastore, sim['nsdid']) 
    
    assert nsd.sim_time_limit == 1000
       
    