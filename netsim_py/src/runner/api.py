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

class ClientError(Error): pass   # These correspond to 4xx status codes

class BadRequest(ClientError): pass
class NotFound(ClientError): pass
class Unauthorized(ClientError): pass
class Forbidden(ClientError): pass
class Conflict(ClientError): pass 

class ServerError(Error): pass  # These correspond to 500 


def apierror(func):
	"""A decorator ensuring that any exception
 	thrown by the wrapped function, is an instance of Error. 
	This is done by passing through all instances of Error, but turning
	(and logging) all others into ServerError
	"""
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Error:
			raise
		except Exception as e:
			logging.debug("Mapping exception to BadRequest",exc_info=1)
			raise BadRequest("Unexpected error", repr(e))
	return wrapper

_repoerror_map = [
	(dpcmrepo.GenericError , Forbidden),
	(dpcmrepo.Conflict , Conflict),
	(dpcmrepo.NotFound , NotFound),
	(dpcmrepo.BadRequest , BadRequest),
	(dpcmrepo.AuthenticationFailed , Unauthorized),
	(dpcmrepo.Error, ServerError)	
]

def map_repository_error(e):
	"""
	For e an instance of dpcmrepo. Error, map it into an appropriate instance
	of api.Error and raise it.
	"""
	assert isinstance(e, dpcmrepo.Error)
	for repocls, apicls in _repoerror_map:
		if isinstance(e, repocls):
			raise apicls(* e.args)
	assert False

def repoerror(func):
	"""A decorator that wraps the method, ensuring that any exception
 	thrown is an instance of Error. 

	This method translates all dpcmrepo. Error instances
	into corresponding api.Error instances and turns all 
	others into ServerError.
	"""
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Error:
			raise
		except dpcmrepo.Error as e:
			logging.debug("Mapping repository exception", exc_info=1)
			map_repository_error(e)
		except Exception as e:
			logging.debug("Mapping exception to BadRequest",exc_info=1)
			raise BadRequest("Unexpected error", repr(e))
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
		raise ValueError("Cannot find NSD with id = '%s'" % nsdid)

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
			'simulation_status': 'INIT'
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



@repoerror
def get_simulation(simid):
	'''Read the simulation object from the PR.'''
	sim = repo().SIM.get(simid)
	if sim.get('type', None) != "simoutput":
		raise NotFound("There is no simulation with this id")
	return sim


@repoerror
def delete_simulation(simid):
	'''Delete a simulation. This fails if the simulation is still running.

	'''
	simdb = repo().SIM

	try:
		sim = simdb.get(simid)
		if sim.get('type', None) != "simoutput":
			raise NotFound("There is no simulation with this id")
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


@repoerror
def get_projects():
	'''Return an iterator on all projects'''
	return repo().get_projects()

@repoerror
def get_plans(prjid):
	'''Return an iterator on all plans for a given project'''
	return repo().get_plans(prjid)

@repoerror
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


	def findAll(self, reduced = True):
		'''
		Return a list of all documents.

		If reduced is given, return an iterator of 'reduced' documents.
		Else, return an iterator returning the full documents.
		'''
		return self.findBy('all',reduced=reduced)

	@repoerror
	def findBy(self, view, key=None, reduced=True):
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
		for rec in qry:
			yield rec[attr]

	@repoerror
	def create(self, obj):
		if 'type' not in obj:
			obj['type'] = self.type
		elif obj['type'] != self.type:
			raise BadRequest('Wrong type for object to create')

		if self.entity.primary_key and '_id' in obj:
			raise BadRequest("Cannot provide id for object with a primary key.")
		try:
			obj['_id'] = self.model.entity.create_id(obj)
		except Exception as e:
			message="In create(obj): could not create id for object."
			details="The exception was: %s" % str(e)
			raise BadRequest(message=message, details=details)

		return self.__db().save(obj)		

	@repoerror
	def read(self, oid):
		obj = self.__db().get(oid)
		if obj.get('type', None) != self.type:
			raise NotFound('Object of wrong type was passed')
		return obj

	@repoerror
	def update(self, oid, obj):
		# Couchdb does not have the concept of update, but we
		# still need to check consistency.
		obj['_id'] = oid
		try:
			# check primary key change
			if self.entity.primary_key:
				if self.entity.create_id(obj)!=oid:
					raise BadRequest("Cannot change the primary key attributes")
			return self.__db().save(obj)
		except dpcmrepo.Conflict as e:
			# try to read the current object
			cur = self.__db().get(oid)
			raise Conflict(current_object = cur) from e

	@repoerror
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




