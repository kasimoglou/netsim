'''
	A datastore used for testing
'''


import os.path, errno, argparse, logging, sys, shutil, json

from urllib.parse import urlparse, urlunparse
from simgen.datastore import DataStore, register_datastore_proxy
from simgen.utils import get_file, put_file

class FileStore(DataStore):
    """A datastore accessing data from a local filesystem directory.
    
    This datastore is mainly intended to be used for code generator development.
    """
    def __init__(self, url):
        '''Initialize.
        
        url - url of the root object
        '''        
        super().__init__(url)
        purl = self.parsed_root_url
        if purl.scheme != 'file':
            raise ValueError("Invalid scheme %s (file expected)" % purl.scheme)
        if purl.netloc != "":
            raise ValueError("Unsupported file url with network location: %s" % purl.netloc) 
        if not os.path.isabs(purl.path):
            raise ValueError("Root url must be an absolute path")
        
        self.root_path = purl.path
        self.root_dir = os.path.abspath(os.path.dirname(purl.path))            
    
    
    def abspath(self, path):
        """Return an absolute path for the given path.

        If the path is relative, it is interpreted as a sibling of the root object.
        For example:
          if the root_path is  "/my/path/nsd.json", 
          then abspath("foo/bar")  returns "/my/path/foo/bar"
        """        
        if not os.path.isabs(path):
            return os.path.join(self.root_dir, path)
        else:
            return path
    
    def get_json_object(self, path):
        """Return contents of a json file, as a python object."""
        rojson = get_file(self.abspath(path))
        ro = json.loads(rojson)
        return ro

    def put_json_object(self, obj, path):
        """Return contents of a json file, as a python object."""
        fpath = os.path.normpath(self.abspath(path))
        assert fpath.startswith(self.root_dir)
        rpath = os.path.join(os.getcwd(), fpath[len(self.root_dir)+1:])
        ro = json.dumps(obj)
        put_file(rpath, ro)

    
    def url_to_path(self, url):
        if isinstance(url, str):
            url = urlparse(url)
        if url.scheme != "file":
            raise ValueError("Url scheme is not 'file'")
        return os.path.normpath(self.abspath(url.path))
            
    
    def __get_object(self, url):
        """Get json object for given url"""
        return self.get_json_object(self.url_to_path(url))        
    
    def get_root_object(self):
        """Read the root object.
            
        The object is returned by parsing the json content of the root object.
        """
        return self.get_json_object(self.root_path)

    def put_root_object(self, sim):
        """Update root object with the fields of the passed sim, which must be a
        map-like object."""
        robj = self.get_json_object(self.root_path)
        robj.update(sim)
        self.put_json_object(robj, self.root_path)


    def get(self, entity, oid):
        '''
        Read an entity from the file store. Basically, ignore the entity
        and just read the object (also take care of attachments).
        '''
        if isinstance(oid, (tuple,list)):
            oid = oid[1]
        return self.__get_object(oid)

register_datastore_proxy('file', FileStore)

