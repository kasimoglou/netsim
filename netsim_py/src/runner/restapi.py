'''
Created on Mar 3, 2014

@author: vsam
'''


import sys, json
import logging
import bottle
from bottle import run, route, view, static_file, post, request, response, HTTPResponse
from runner import api

##############################################
#
# ReST API. This is a restful front-end to
#  the server api. 
#
##############################################



def json_abort(code, msg=None, **kwargs):
	'''Raise an http error with a json response body.'''

	body = {
		'status':code, 
		'message': bottle.HTTP_CODES[code] if msg is None else str(msg),
		'details': 'No information is available for this problem'
	}
	body.update(kwargs)
	logging.error("json_abort: body=%s\n    kwargs=%s", json.dumps(body, indent=4), str(kwargs))
	raise bottle.HTTPResponse(status = code, body = json.dumps(body))


def process_api_error(ex):
	'''
	Raise an HTTPError for the given api Error.
	'''

	# get the error code
	if not isinstance(ex, api.Error):
		logging.debug("In process_api_error: exception class = %s", ex.__class__, exc_info=1)
		json_abort(500, details = 'An unanticipated error occurred. '
			'This is a problem that the server is unable to describe.')
	else:
		code = getattr(ex, 'httpcode')
		msg = bottle.HTTP_CODES[code]
		if 'details' not in ex.kwargs:			
			details = ' '.join(str(arg) for arg in ex.args)
			json_abort(code, msg, details, ** ex.kwargs)
		else:
			json_abort(code, ** ex.kwargs)




app = bottle.Bottle()


@app.post('/simulation')
def POST_simulation():
	'''
	Create a simulation in the process repository and start it in the Manager.
	'''
	#postdata = request.body.read()
	nsdid = request.forms.get("nsdid")
	try:
		logging.info("Requesting simulation for nsd=%s",nsdid)
		sim = api.create_simulation(nsdid)
		response.status = 201   # Created
		return sim
	except ValueError as e:
		logging.warn(* e.args)
		json_abort(403, "The provided NSD id was not legal", 
			details="The project repository does not contain the NSD that was requested"
			"in the simulation: %s" % nsdid)
	except Exception as e:
		process_api_error(e)


@app.get('/simulation/<simid>')
def GET_simulation(simid):
	'''
	Return a simulation object.
	'''
	# Parse object ID
	try:
		return api.get_simulation(simid)
	except Exception as e:
		process_api_error(e)	


@app.delete('/simulation/<simid>')
def DELETE_simulation(simid):
	'''
	Delete a simulation object.
	'''
	# Parse object ID
	try:
		response.status = 204   # NoContent
		return api.delete_simulation(simid)
	except Exception as e:
		process_api_error(e)	


#
# These endpoints are kept for compatibility with the initial versions of the
# nsd editor
#

@app.get('/projects')
def GET_projects():
	try:
		# A small bug: add the 'id' field to be a copy of '_id', to simulate old behaviour
		projects = list(api.project_dao.findAll())
		for p in projects:
			p['id'] = p['_id']
		return { 'results': projects }
	except Exception as e:
		logging.exception('in getting projects from the PR')
		process_api_error(e)

			
					
@app.get('/project/<prjid>/plans')
def get_plans(prjid):
		try:
			project = api.project_dao.read(prjid)
		except api.NotFound:
			logging.exception('in getting projects from the PR')
			json_abort(404, "Cannot find project", 
				details="The requested project does not exist in the repository")
		except api.Unauthorized:
			logging.exception('in getting projects from the PR')
			json_abort(401, "Cannot find project", 
				details="You do not have permission to access the requested project.")
		except Exception as e:
			process_api_error(e)


		logging.root.debug('Project=%s', json.dumps(project, indent=4) )
		plan_ids = project.get('plans',[])
		plans = []

		for plan_id in plan_ids:
			resp = []
			try:
				resp = list(api.plan_dao.findBy('all', key=plan_id))
			except:
				# We failed looking up some plan!
				pass
			if resp:
				assert len(resp)==1
				plans.append(resp[0])
		return { 'results': plans }


class RestApi:
	def __init__(self, dao):
		self.dao = dao
		self.entity = dao.model.entity
		self.views = {view.key.name : view.name for view in dao.model.views}
		self.route()


	def route(self):
		if self.entity.read:
			app.get('/%s' % self.dao.type)(self.GETALL)		
			app.get('/%s/<oid>' % self.dao.type)(self.GET)
		if self.entity.create:
			app.post('/%s' % self.dao.type) (self.POST)
		if self.entity.update:
			app.put('/%s/<oid>' % self.dao.type) (self.PUT)
		if self.entity.delete:
			app.delete('/%s/<oid>' % self.dao.type) (self.DELETE)

	def GETALL(self):
		reduced = not (request.query.reduced in ('no','false','0'))
		view = None
		for v in self.views:
			if v in request.query:
				view = self.views[v]
				break
		if view:
			key = request.query[v]
		try:
			if view is None:
				obj = self.dao.findAll(reduced=reduced)
			else:
				obj = self.dao.findBy(view, key=key, reduced=reduced)
			return { 'results' : list(obj) }
		except Exception as e:
			process_api_error(e)			

	def GET(self, oid):
		try:
			obj = self.dao.read(oid)
			logging.debug('Returning %s',obj)
			return obj
		except Exception as e:
			process_api_error(e)			

	def POST(self):
		try:
			obj = request.json
			if obj is None:
				raise BadRequest()
		except:
			json_abort(400, details='Bad create (POST) request. A json body '
				'was expected but not provided')
		try:
			response.status = 201   # Created
			return self.dao.create(obj)
		except Exception as e:
			try:
				return process_api_error(e)
			except Exception as ne:
				process_api_error(e)

	def PUT(self, oid):
		obj = request.json
		if obj is None:
			json_abort(400, details='Bad update (PUT) request. A json body was expected but not provided')

		try:
			return self.dao.update(oid, obj)
		except Exception as e:
			process_api_error(e)

	def DELETE(self, oid):
		try:
			response.status = 204    # NoContent
			return self.dao.delete(oid)
		except Exception as e:
			process_api_error(e)


#
# Create restful api for all ApiEntity entities in models.project_repo
#
from models.project_repo import ENTITIES, ApiEntity
for e in ENTITIES:
	if isinstance(e, ApiEntity):
		dao = getattr(api, e.dao_name) 
		globals()["%s_api" % e.name] = RestApi(dao)
		logging.info("Installed restful api for entity %s",e.name)


