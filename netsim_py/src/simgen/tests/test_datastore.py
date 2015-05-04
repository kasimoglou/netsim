'''
Unit tests for datastores

Created on Oct 14, 2014

@author: vsam
'''
from simgen.datastore import create_datastore_proxy


#
#  filestore
#

from os.path import join, normpath
from tempfile import mkdtemp
from simgen.utils import put_file


#
#  Testing FileStore
#


def setup_module():
    global root_dir
    root_dir = mkdtemp(dir="/tmp")
    
    SIM="""\
{
    "name": "test_sim",
    "generator": "Castalia",
    "nsd": "file:nsd.json"
}
"""
    NSD="""\
{
    "sim_time_limit": 1000
}
"""

    put_file( join(root_dir, "sim.json"), SIM )
    put_file( join(root_dir, "nsd.json"), NSD )



def teardown_module():
    import os
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


def get_filestore_in_resources():
    global root_dir
    sjpath = join(root_dir,"sim.json")
    return create_datastore_proxy("file://"+sjpath)

def test_filestore_attr():
    ds = get_filestore_in_resources()
    
    assert ds.root_path == join(root_dir, "sim.json")
    assert ds.root_dir == root_dir


def test_filestore_abspath():
    ds = get_filestore_in_resources()

    assert ds.abspath("foo") == join(root_dir, "foo")
    assert ds.abspath("nsd.json") == join(root_dir,"nsd.json")
    assert normpath(ds.abspath(".")) == root_dir
    assert normpath(ds.abspath("..")) == "/tmp"
     

def test_filestore_url_to_path():
    ds = get_filestore_in_resources()    
    assert ds.url_to_path("file:nsd.json")==join(root_dir, "nsd.json" )
    assert ds.url_to_path("file:.") == root_dir
    assert ds.url_to_path("file:..") == "/tmp"

def test_filestore_load_root_object():
    ds = get_filestore_in_resources()    
    sim = ds.get_root_object()

    assert 'generator' in sim
    assert 'name' in sim
    assert 'nsd' in sim

    assert sim['nsd']=="file:nsd.json"

def test_filestore_load_relative_path():        
    ds = get_filestore_in_resources()

    sim = ds.get_root_object()
    nsd_obj = ds.get_nsd(sim['nsd'])
    assert 'sim_time_limit' in nsd_obj
    
        

