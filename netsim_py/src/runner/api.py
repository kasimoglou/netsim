'''
    The runtime API.

    This is the place where the components combine to expose the public netsim service api
'''

from runner.DAO import SimJob
from runner.monitor import Manager
from runner import dpcmrepo
from runner.dpcmrepo import repo, repo_url
from runner.config import cfg
from runner.apierrors import *
from simgen.gen import validate_simulation
from models.project_repo import NSD, VECTORL, ApiEntity

import runner.AAA as AAA

import os, logging, functools
import os.path, json

_repoerror_map = {
    dpcmrepo.GenericError : Forbidden,
    dpcmrepo.Conflict : Conflict,
    dpcmrepo.NotFound : NotFound,
    dpcmrepo.BadRequest : BadRequest,
    dpcmrepo.AuthenticationFailed : Unauthorized,
}


logger = logging.getLogger("API")


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
                logger.error("An unknown dpcmrepo.ApiError subclass was encountered: ", 
                    e.__class__.__name__)
                # Just do a default thing
                raise ServerError(*e.args, details="An unexpected problem with the project repository"
                    " was encountered.") from e

        except BaseException as e:
            logger.debug("Mapping exception to BadRequest",exc_info=1)
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
        raise BadRequest(details='The specified NSD does not reference a project!'
        ' This is definitely a malformed NSD, and a simulation cannot be created for it.')
    try:
        plan_id = nsd['plan_id']
    except KeyError:
        raise BadRequest(details='The specified NSD does not specify a plan. Therefore, the ' 
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
    logger.info("Created simulation with url=%s",url)

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
        logger.debug('In api.delete_simulation(%s)',simid, exc_info=1)
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


@apierror
def validate_nsd(nsd_id):
    '''
    Return a json object with the results of running NSD validation.
    '''
    try:
        url = repo().url_of(NSD, nsd_id)
        results = validate_simulation(url)
    except Exception as e:
        logger.error("Unexpected exception from validate_simulation()", exc_info=1)
        raise ServerError(details="An unexpected exception occurred during NSD validation")

    return results



@apierror
def nsd_editor_path(model, oid):
    assert isinstance(model, ApiEntity)
    prefix = "/nsdEdit"
    if model is NSD:
        return ''.join((prefix,"/html/index.html#!/nsd/",oid))
    elif model is VECTORL:
        return ''.join((prefix,"/html/index.html#!/vectorl/",oid))


#
# User management
#

@apierror
def create_user(user):
    '''Create a new system user.'''
    roles = AAA.session_roles()
    if not AAA.UserRecord.authorize(roles, AAA.Create):
        raise Unauthorized(details="Not authorized to create users")
    Manager.create_user(user)
    logger.info("New system user: %s", user.username)

@apierror
def delete_user(username):
    '''Delete a system user.'''
    roles = AAA.session_roles()
    if AAA.current_user()==username:
        roles.add(AAA.Owner)
    if not AAA.UserRecord.authorize(roles, AAA.Delete):
        raise Unauthorized(details="Not authorized to delete users")
    Manager.delete_user(username)
    logger.info("Deleted user: %s", username)

@apierror
def change_user_password(username, password):
    '''Change the password for a user.'''
    roles = AAA.session_roles()
    if AAA.current_user()==username:
        roles.add(AAA.Owner)
    if not AAA.UserRecord.authorize(roles, AAA.ChangeUserPassword):
        raise Unauthorized(details="Not authorized to change the password for this user")
    Manager.update_user(username, password=password)
    logger.info("Changed password for user: %s", username)

@apierror
def change_admin_status(username, is_admin):
    '''Change the admin status of a user.'''
    roles = AAA.session_roles()
    if AAA.current_user()==username:
        roles.add(AAA.Owner)
    if not AAA.UserRecord.authorize(roles, AAA.ChangeAdminStatus):
        raise Unauthorized(details="Not authorized to change the admin flag for this user")
    Manager.update_user(username, is_admin=is_admin)
    logger.info("Changed admin status for user '%s' to %s", username, is_admin)

@apierror
def verify_password(username, password):
    return Manager.get_user(username).password==password

@apierror
def login(username, password):
    # No password at this time
    success = username and verify_password(username, password)

    if success:
        AAA.set_current_user(username)
        logger.info('User %s logged in', username)
    else:
        logger.info("Login failure: username='%s'", username)
    return success

@apierror
def logout():
    AAA.clear_current_user()




#
# Pass-through CRUD API for project repository
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
                logger.debug("Fetch field %s", ff.name)
                if ff.fkey.name not in obj:
                    continue
                fid = obj[ff.fkey.name]
                dao = globals()[ff.fkey.references.dao_name]
                fobj = list(dao.findBy('all', key=fid, reduced=True, fetch=False))
                assert len(fobj)<=1
                if len(fobj):
                    obj[ff.name] = fobj[0]
                else:
                    logger.warn("Foreign key is stale for %s", obj.get('_id', "<unknown>"))
            except:
                # log but otherwise ignore errors
                logger.exception("Failed to fetch join field '%s' for %s", 
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
                logger.exception("Failed to fetch join field '%s' for %s", 
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

        init_obj = self.entity.initialize(obj)
        logger.debug("New entity=", init_obj)

        try:
            newobj = self.__db().save(init_obj)
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
        logger.info("Installed CRUD api for entity %s",e.name)
_create_crud_api()


#
# Initializers
#

# This assures delayed initialization
predefined_plots = None
def _get_predefined_plots():
    global predefined_plots
    if predefined_plots is None:
        with open(os.path.join(cfg.resource_path, 'datavis/predefined_plots.json'), 'r') as f:
            predefined_plots = json.load(f)
    return predefined_plots


# make nsd initially runnable (if possible!)
# we are still in need of a current plan and current user!
def _nsd_init(entity, obj):

    # (0) project id
    if 'current_project' in AAA.session():
        obj.setdefault('project_id', AAA.session()['current_project'])

    # (A) parameters
    obj.setdefault('parameters', {})
    obj['parameters'].setdefault('sim_time_limit', 3600)
    obj['parameters'].setdefault('simtime_scale', -9)

    # (B) environment
    obj.setdefault('environment',{})
    obj['environment'].setdefault('type','castalia')

    # (C) network
    if 'current_plan' in AAA.session():
        obj.setdefault('plan_id', AAA.session()['current_plan'])

    # (D) views
    obj.setdefault('views', _get_predefined_plots()['views'])

    logger.debug("NSD initialized to: ", obj)

    return obj

def _add_initializers():
    from models.project_repo import NSD
    NSD.initializer = _nsd_init
_add_initializers()

#
# Vectorl compilation and running
#

from vectorl.repofactory import proc_vectorl_model

@apierror
def process_vectorl(vectorl_id, run=False, until=None, steps=1000):
    # put a maximum cutoff at the number of steps!
    max_steps = 100000
    if steps is not None and steps>max_steps:
        raise Forbidden(details="The number of simulation steps requested exceeds the allowable maximum of %d" % max_steps)

    vlres = list(vectorl_dao.findBy('all', key=vectorl_id))
    if len(vlres)==0:
        raise NotFound(details="The requested vectorl object does not exist")
    assert len(vlres)==1

    vlobj = vlres[0]
    project_id = vlobj['project_id']
    name = vlobj['name']

    return proc_vectorl_model(project_id, name, run, until=until, steps=steps)
