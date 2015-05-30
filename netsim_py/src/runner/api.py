'''
    The runtime API.

    This is the place where the components combine to expose the public netsim service api
'''

from runner.DAO import SimJob
from runner.monitor import Manager
from runner import dpcmrepo
from runner.dpcmrepo import repo
import os, logging, functools
from runner.config import cfg


# Exceptions thrown by the API. These resemble HTTP errors closely.

class Error(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(self, args)
        self.kwargs = kwargs
        if 'details' not in kwargs:
            self.kwargs['details'] = self.details
        if args and 'hint' not in kwargs:
            self.kwargs['hint'] = ','.join(args)

    def __repr__(self):
        return "%s(%s , %s)" % (self.__class__.__name__, self.args, self.kwargs)

class ClientError(Error):   # These correspond to 4xx status codes
    httpcode = 400

class BadRequest(ClientError):
    httpcode = 400
    details = 'Something was wrong with your request.' \
        ' Unfortunately there are no more details.'

class NotFound(ClientError):
    httpcode = 404
    details = 'The requested object does not exist in the '\
            'project repository.'

class Unauthorized(ClientError):
    httpcode = 401
    details = 'You are not authorized to perform this operation.'\

class Forbidden(ClientError):
    httpcode = 403
    details = 'The project repository has forbidden this operation'\

class Conflict(ClientError):
    httpcode = 409
    details = 'There is a conflict in the project repository, '\
        'maybe someone is also editing the same data.'

class ServerError(Error): # These correspond to 500 
    httpcode = 500
    details = 'There was a server error during the operation. Please '\
        'retry the operation, or consult the system administrator.'


_repoerror_map = {
    dpcmrepo.GenericError : Forbidden,
    dpcmrepo.Conflict : Conflict,
    dpcmrepo.NotFound : NotFound,
    dpcmrepo.BadRequest : BadRequest,
    dpcmrepo.AuthenticationFailed : Unauthorized,
}



def apierror(func):
    """
    A decorator ensuring that any exception
    thrown by the wrapped function, is an instance of Error.

    This is done by passing through all instances of Error, mapping 
    dpcmrepo.Error instances to api.Error types and instances and
    turning (and logging) all others into ServerError.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error:
            raise

        except dpcmrepo.ApiError as e:
            if e.__class__ in _repoerror_map:
                api_exc = _repoerror_map[e.__class__]
                raise api_exc(* e.args) from e
            else:
                logging.error("An unknown dpcmrepo.ApiError subclass was encountered: ", 
                    e.__class__.__name__)
                # Just do a default thing
                raise ServerError(*e.args, details="An unexpected problem with the project repository"
                    " was encountered.") from e

        except BaseException as e:
            logging.debug("Mapping exception to BadRequest",exc_info=1)
            raise BadRequest(details="An unexpected error in the server has occurred")
    return wrapper



#
# API methods
#

def create_simoutput(xtor, prepo, nsdid):
    '''Given executor xtor, project repository prepo
    and an nsdid file, create a new simoutput object.

    Returns a triple: (sim, url, simhome), where:
    sim is the json object created
    url is the complete url in the project repository
    simhome is the absolute path to the simulation home
    '''

    # Get the PR database and check that the NSD exists
    simdb = prepo.SIM
    if nsdid not in simdb:
        raise NotFound(nsdid, details= "Cannot find the spcified NSD in the project")

    # Get the nsd
    nsd = simdb.get(nsdid)
    # extract project and plan id
    try:
        project_id = nsd['project_id']
    except KeyError:
        raise BadRequest('The specified NSD does not reference a project!'
        ' This is definitely a malformed NSD, and a simulation cannot be created for it.')
    try:
        plan_id = nsd['plan_id']
    except KeyError:
        raise BadRequest('The specified NSD does not specify a plan. Therefore, the ' 
            'simulation cannot be created. Try to edit the NSD in the NSD editor.')


    # Create the homedir
    simhome = xtor.create_home_directory()

    try:
        # create sim id
        simid = SimJob.make_simid(xtor.name, simhome)

        # remove any old sims by this name
        try:
            oldsim = simdb.get(simid)
            simdb.delete(oldsim)
        except dpcmrepo.NotFound:
            pass

        # create the new sim
        sim = simdb.save({ 
            '_id' :  simid,
            'type' : 'simoutput',
            'nsdid' : nsdid, 
            'generator': 'Castalia',
            'simulation_status': 'INIT',
            'plan_id': plan_id,
            'project_id': project_id            
        })
    except:
        # we failed to create the sim object, delete the simhome and re-raise
        os.rmdir(simhome)
        raise

    url = "%s/%s" % (simdb.resource.base_url, sim['_id'])
    logging.info("Created simulation with url=%s",url)

    return sim, url, simhome


@apierror
def create_simulation(nsdid, xtorname=None):
    '''
    Create a simulation in the project repository and start a job for it.
    nsdid - the id of the NSD for the new simulation
    Return the new sim object created.
    Raises ValueError if nsdid is not in database PR.SIM
    '''

    # Get the executor
    xtor = Manager.executor(xtorname)

    # create the simoutput object
    sim, url, simhome = create_simoutput(xtor, repo(), nsdid)
    
    # create the job
    Manager.create_job(xtor, url, simhome)
    return sim



@apierror
def get_simulation(simid):
    '''Read the simulation object from the PR.'''
    sim = repo().SIM.get(simid)
    if sim.get('type', None) != "simoutput":
        raise NotFound("There is no simulation with this id")
    return sim


@apierror
def delete_simulation(simid):
    '''Delete a simulation. This fails if the simulation is still running.

    '''
    simdb = repo().SIM

    try:
        sim = simdb.get(simid)
        if sim.get('type', None) != "simoutput":
            raise NotFound(details="There is no simulation with this id")
        simdb.delete(simid)
    except (dpcmrepo.NotFound,NotFound):
        logging.debug('In api.delete_simulation(%s)',simid, exc_info=1)
        pass # Ignore 

    # Now, get the job
    simjob = Manager.get_job_by_simid(simid)

    if simjob is None:
        raise NotFound("There is no simulation with this id")

    if simjob.state != 'PASSIVE':
        raise BadRequest("Cannot delete unfinished simulation")

    Manager.delete_job(simid)


@apierror
def get_projects():
    '''Return an iterator on all projects'''
    return repo().get_projects()

@apierror
def get_plans(prjid):
    '''Return an iterator on all plans for a given project'''
    return repo().get_plans(prjid)

@apierror
def get_nsds():
    '''Return an iterator on all projects and NSD for it.
    '''
    return repo().get_nsds()



#
# Pass-through CRUD API
#
class RepoDao:
    '''
    This class implements a set of methods that provide a standard CRUD api
    to a type of object.
    '''
    def __init__(self, model):
        self.model = model
        self.entity = entity = model.entity
        self.type = entity.name
        self.db = entity.database.name

        # index the views
        self.views = {
            view.name: view  for view in model.views
        }

        self.unique = entity.unique

    def __db(self):
        return repo().database(cfg[self.db])

    def join_fetch_fields_for_object(self, obj):
        '''
        This is used only for one object.
        '''
        for ff in self.entity.fetch_fields:
            try:
                logging.debug("Fetch field %s", ff.name)
                if ff.fkey.name not in obj:
                    continue
                fid = obj[ff.fkey.name]
                dao = globals()[ff.fkey.references.dao_name]
                fobj = list(dao.findBy('all', key=fid, reduced=True, fetch=False))
                assert len(fobj)<=1
                if len(fobj):
                    obj[ff.name] = fobj[0]
                else:
                    logging.warn("Foreign key is stale for %s", obj.get('_id', "<unknown>"))
            except:
                # log but otherwise ignore errors
                logging.exception("Failed to fetch join field '%s' for %s", 
                    ff.name, obj.get('_id', "<unknown>"))
        return obj

    def join_fetch(self, objiter):
        objects = list(objiter)
        if len(objects)==0: return
        # "Threshold" == 2
        if len(objects)<2:
            for obj in objects:
                yield self.join_fetch_fields_for_object(obj)
            return
        # more than "Threshold" objects, we should do a join.
        # (a) build indices over all joined sets

        join_obj = {}
        for ff in self.entity.fetch_fields:
            # for each ff create a map id->obj and put the map in 
            # join_obj, under the ff name
            try:
                dao = globals()[ff.fkey.references.dao_name]
                fobj_list = dao.findAll(reduced=True, fetch=False)
                idx_fobj = {}
                for fobj in fobj_list:
                    idx_fobj[fobj['_id']] = fobj
                join_obj[ff.name] = idx_fobj
            except:
                # log but otherwise ignore errors
                logging.exception("Failed to fetch join field '%s' for %s", 
                    ff.name, obj.get('_id', "<unknown>"))

        # (b) Generate an index-loop join result
        for obj in objects:
            for ff in self.entity.fetch_fields:
                if ff.name not in join_obj: continue
                if ff.fkey.name not in obj: continue
                fkey = obj[ff.fkey.name]
                if fkey in join_obj[ff.name]:
                    obj[ff.name] = join_obj[ff.name][fkey]
            yield obj


    def drop_fetch_fields(self, obj):
        for ff in self.entity.fetch_fields:
            if ff.name in obj:
                del obj[ff.name]
        return obj

    def findAll(self, reduced = True, fetch=True):
        '''
        Return a list of all documents.

        If reduced is given, return an iterator of 'reduced' documents.
        Else, return an iterator returning the full documents.
        '''
        return self.findBy('all',reduced=reduced, fetch=fetch)

    @apierror
    def findBy(self, view, key=None, reduced=True, fetch=True):
        if view not in self.views:
            raise BadRequest('View does not exist')
        resource = self.views[view].resource
        kwds = {}
        if not reduced:
            kwds['include_docs'] = True
        if key is not None:
            kwds['key'] = str(key)
        qry = self.__db().query(resource, **kwds)
        attr = 'value' if reduced else 'doc'
        if fetch:
            yield from self.join_fetch(rec[attr] for rec in qry)
        else:
            for rec in qry:
                yield rec[attr]

    @apierror
    def create(self, obj):
        if 'type' not in obj:
            obj['type'] = self.type
        elif obj['type'] != self.type:
            raise BadRequest('Wrong type for object to create')

        if self.entity.primary_key and '_id' in obj:
            raise BadRequest(message="Id provided for object with automatic id.",
            details="You cannot provide an id for this type of object, the id will be"
            " created automatically.")
        try:
            obj['_id'] = self.model.entity.create_id(obj)
        except Exception as e:
            message="In create(obj): could not create id for object."
            details="While creating an object, failed to create the id for the object. \
Is the name of the object 'strange'? The exception was: %s" % str(e)
            raise BadRequest(message=message, details=details)

        try:
            newobj = self.__db().save(obj)
        except dpcmrepo.Conflict as e:
            # Conflict at creation means the same primary key
            raise Conflict(details="There is already an object with this name "
                "in the project repository") from e

        return self.join_fetch_fields_for_object(newobj)

    @apierror
    def read(self, oid):
        obj = self.__db().get(oid)
        if obj.get('type', None) != self.type:
            raise NotFound(details='An object with this id was found in the project repo, '
                'but it has wrong type.')
        return self.join_fetch_fields_for_object(obj)

    @apierror
    def update(self, oid, obj):
        # Couchdb does not have the concept of update, but we
        # still need to check consistency.
        obj = self.drop_fetch_fields(obj)
        obj['_id'] = oid        
        try:
            # check primary key change
            if self.entity.primary_key:
                if self.entity.create_id(obj)!=oid:
                    raise BadRequest("Cannot change the primary key attributes",
                        details="The update attempted to change some non-changeable "
                        "field in the object, therefore it has failed.")
            return self.__db().save(obj)
        except dpcmrepo.Conflict as e:
            # try to read the current object
            cur = self.read(oid)
            raise Conflict(message="Conflict in object update", current_object = cur, 
                details = "The update has failed because of a conflict at the "
                "project repository. Maybe someone is editing the object at the"
                " same time.") from e

    @apierror
    def delete(self, oid):
        # Remove any sentinels for this object
        self.__db().delete(oid)



#
# Create crud api for all ApiEntity entities in models.project_repo
#

def _create_crud_api():
    from models.project_repo import MODELS
    for em in MODELS:
        e = em.entity
        globals()[e.dao_name] = RepoDao(em)
        logging.info("Installed CRUD api for entity %s",e.name)
_create_crud_api()




