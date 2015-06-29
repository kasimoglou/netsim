'''
This module contains code for fetching and storing simulation data from
and into a variety of datastores, e.g., the project repository, or the
file system.

Created on Sep 24, 2014

@author: vsam
'''


import os.path, json, logging
from urllib.parse import urlparse, urlunparse, urldefrag

from models.project_repo import SIM
from simgen.validation import *
from runner import dpcmrepo, config
from simgen.utils import get_file, put_file, execute_function

from io import StringIO


logger = logging.getLogger('codegen')


def set_root_url(fileloc, url):
    """Store the root url into the simulation home.
    """
    put_file(os.path.join(fileloc, 'url.txt'), url)


def get_root_url(fileloc):
    """Return the root url given the simulation home.
    """
    return get_file(os.path.join(fileloc, 'url.txt'))
        



class DataStore:
    """Base class for datastores.
    
    A datastore is a proxy object via which the code generator accesses the project repository
    or, in general, any data source for retrieving the full NSD.  
    """
    def __init__(self, root_url):
        """Initialize.
        
        The root_url must be either a string or an object returned by
        urllib.parse.urlparse() 
        """
        super().__init__()
        if isinstance(root_url, str):
            self.root_url = root_url
            self.parsed_root_url = urlparse(root_url)
        elif hasattr(root_url, "scheme"):
            self.root_url = root_url.geturl()
            self.parsed_root_url = root_url
        else:
            raise TypeError("root_url must be either string or returned from urllib.parse.urlparse()")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return exc_type is None

    #
    # Datastore API
    # 

    def get_root_object(self):
        """Return a dict with the fields of the root object"""
        raise NotImplementedError

    def put_root_object(self, sim):
        """Update root object with the fields of the passed sim, which must be a
        map-like object."""
        raise NotImplementedError

    def update_root_object(self, newsim=(), **kwargs):
        """Update root object with the fields passed. newsim and kwargs are passed to
        method dict.update(), that is, newsim is either a map-like object, or a sequence 
        of pairs.

        Returns the updated simulation object.
        """
        sim = self.get_root_object()
        sim.update(newsim, **kwargs)
        self.put_root_object(sim)
        return sim

    def get(self, entity, oid):
        """Retrieve plan for the given oid"""
        raise NotImplementedError



class ProjectRepoStore(DataStore):
    """The datastore used to access the project repository.
    """
    def __init__(self, root_url, repo=None):
        '''
        Create a Project Repository Datastore.
        '''
        super().__init__(root_url)
        assert self.parsed_root_url.scheme  in ('http','https')
        
        # construct url for repo
        scheme = self.parsed_root_url.scheme
        netloc = self.parsed_root_url.netloc

        self.repo_url = urlunparse((scheme, netloc, '', '', '', ''))

        # Get couchdb database
        if repo is None:
            self.repo = dpcmrepo.ProjectRepository(self.repo_url)
        else:
            self.repo = repo
        self.ptdb = self.repo.PT
        self.simdb = self.repo.SIM
        
        # The simulation id is the last element of the url of the root object
        self.sim_id = os.path.basename(self.parsed_root_url.path)
        logger.debug("Datastore initialized: %s\n%s", self.parsed_root_url.path, self.sim_id)


    def get_root_object(self):
        """Read the root object."""
        return self.simdb.get(self.sim_id)
        
    def put_root_object(self, sim):
        """Save the root object sim."""
        self.simdb.save(sim)


    def get_attached_file(self, entity, obj, attached):
        """
        Download and save locally an attached text file inside
        an object.
        """
        db = self.repo.db_of(entity)
        try:
            code = db.get_attachment(obj, attached)
            with open(attached, "w") as codefile:
                codefile.write(code.decode('utf8'))
        except dpcmrepo.NotFound:
            fail("Attachment '%s' of type %s does not exist.", attached, entity.name)
            



    def get(self, entity, oid):
        """
        Given an entity from models/project_repo.py and
        an oid, retrieve the object.
        """
        db = self.repo.db_of(entity)

        try:
            if isinstance(oid, (tuple,list)) and len(oid)==2:
                doc, fname = oid
                data = db.get_attachment(doc, fname)
                return json.loads(data.decode('utf-8'))
            else:
                return db.get(oid)
        except dpcmrepo.NotFound:
            fail("The object %s of type %s does not exist in the project repository", oid, entity.name)

    def get_by(self, entity, view, key):
        """
        Given an entity type and a view on it, get the (unique) object whose view
        matches the key, or None, if not found.
        """
        db = self.repo.db_of(entity)
        resource = entity.design.named_view(view).resource

        kwds = {'include_docs': True, 'key': key }
        qry = list( db.query(resource, **kwds) )

        if len(qry)>1:
            fail("There are multiple mappings for the given object")
        if len(qry)==0:
            return None

        return qry[0]['doc']


class NsdValidationRepoStore(ProjectRepoStore):
    def __init__(self, root_url, repo=None):
        '''
        Initialize a datastore for the project repo, without a simulation.
        root_url is actually the url of the nsd in the repostore.
        '''
        super().__init__(root_url, repo)
        # Since root_url is actually the url of the nsd, 
        # some magic is needed both after we call the 
        # parent constructor.
        self.nsdid = self.sim_id
        self.sim_id = None

        self.root_object = {
           "type": "simoutput",
           "generator": "Castalia",
           "nsdid": self.nsdid
        }


    def get_root_object(self):
        """Read the root object."""
        return self.root_object
        
    def put_root_object(self, sim):
        """Save the root object sim."""
        self.root_object = sim


# Mapping from URL scheme to datastore class (module-private)
_SCHEME_TO_DATASTORE = {
    'http': ProjectRepoStore,
    'validate': NsdValidationRepoStore
}


def register_datastore_proxy(scheme, cls):
    _SCHEME_TO_DATASTORE[scheme] = cls

def create_datastore_proxy(url):
    """Return a datastore object for the provided URL.
    
    Currently, this is using the URL schema.
    """

    # defrag the url
    basic_url, fragment = urldefrag(url)
    U = urlparse(basic_url)
    scheme = fragment if fragment else U.scheme
    return _SCHEME_TO_DATASTORE[scheme](U)



class Context:
    """
    An instance of this class is available globally during execution of each task
    of a simulation job, by a call to utils.execute_function(), which runs in its
    own process.

    The instance is created automatically by the call to execute_context().
    """

    def initialize(self):
        """This is called from execute_context(), after forking. Thus, it always
        initializes in a process-specific way.
        """
        self.fileloc = os.getcwd()        
        self.sim_url = get_root_url(self.fileloc)
        self.__datastore = None
        self.__sim_id = None
        self.validate=False

    def finalize(self):
        """Called to clean up the context, before the subprocess ends."""
        pass

    @property
    def datastore(self):
        """Return the datastore for this context."""
        if self.__datastore is None:
            self.__datastore = create_datastore_proxy(self.sim_url)
        return self.__datastore

    @property
    def sim_id(self):
        return self.datastore.sim_id

#
# The context global var
#
context = Context()


def _context_wrapper(func, args, kwargs):
    """Initialize the context for this call."""
    try:
        context.initialize()
        return func(*args, **kwargs)
    finally:
        context.finalize()


def execute_context(fileloc, func, suffix, redir, *args, **kwargs):
    """
    Wrapper for execute_function(), which initializes the global context.
    """
    return execute_function(fileloc, _context_wrapper, suffix, redir, func, args, kwargs)



