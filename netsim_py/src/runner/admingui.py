'''
Created on Mar 13, 2015

@author: vsam
'''


'''
Created on Mar 3, 2014

@author: vsam
'''

import runner.api as api
import runner.AAA as AAA
from runner.config import gui_file_path, cfg
from runner.monitor import Manager
from runner.AAA import User
from runner.dpcmrepo import repo_url

from models.constraints import ConstraintViolation
from models.project_repo import NSD, SIM, PROJECT, PLAN

import sys
import logging, os
import bottle
import os.path
import urllib.request 
import pycouchdb
import json

from bottle import run, route, view, static_file, post, \
					request, HTTPError, redirect, abort
from threading import Thread


#
# A simple decorator for mini-templates that render their doc-string
#

app = bottle.Bottle()

@app.get("/shutdown")
@AAA.logged_in
def page_shutdown():
	def shutdown_thread():
		import time
		logging.info("Shutdown process started")
		Manager.shutdown()
		time.sleep(1)
		logging.critical("Shutdown complete, exiting")
		os._exit(0)
	Thread(target=shutdown_thread).start()
	bottle.redirect("/admin")


@app.get("/logout")
@AAA.logged_in
def dologout():
	api.logout()
	redirect("/admin/login.html")


@app.get('/login.html')
@view("login.html")
def get_login(): 
	#thispage="/admin/login.html"
	return locals()

@app.post('/login.html')
@view("login.html")
def do_login():
	# check user and password
	user = request.forms.login
	password = request.forms.password
	remember_me = request.forms.remember_me

	if api.login(user, password):
		redirect("/admin")
	failure = True
	return locals()


@app.route("/jobs.html")
@view("job_table.html")
@AAA.logged_in
def show_jobs():
	refresh_page = True
	thispage = "/admin/jobs.html"
	return locals()


@app.route("/new_job.html")
@view("new_job.html")
@AAA.logged_in
def show_job_form():
	refresh_page = False
	thispage = "/admin/new_job.html"
	return locals()


@app.post("/jobs.html")
@view("job_table.html")
@AAA.logged_in
def submit_job_url():

	command = request.forms.command
	logging.debug('In POST /jobs.html: %s',command)

	if command=='delete':
		simid = request.forms.simid
		api.delete_simulation(simid)
		logging.info("Deleting job simid=%s", simid)
	else:
		abort(400, "Cannot process request")
	refresh_page = True
	thispage = "/admin/jobs.html"
	return locals()


@app.get("/simfile/<xtor>/<name>/<fname>")
@AAA.logged_in
def get_simfile(xtor, name, fname):
	try:
		executor = Manager.executor(xtor)
		fileloc = os.path.join(executor.homedir, name)
		return static_file(fname, root=fileloc)		
	except:
		logging.info("Cannot find simulation", exc_info=True)
		abort(400, "Cannot find simulation.")


@app.get("/simhomes/<xtor>/<name>")
@view("simhome.html")
@AAA.logged_in
def view_simhome(xtor, name):
	# check that the sim exists
	selected_file = request.query.selected

	try:
		executor = Manager.executor(xtor)
		fileloc = os.path.join(executor.homedir, name)
		job = Manager.get_job_by_fileloc(fileloc)
		if job is None:
			raise KeyError("No such job:", xtor, name)
	except:
		logging.info("Cannot find simulation", exc_info=True)
		abort(400, "Cannot find simulation.")

	job_status = job.status+(("[%s]" % job.last_status) 
		if job.status=='ABORTED' else "")
	job_created = job.tscreated.strftime("%y/%m/%d %H:%M:%S")
	job_runtime = str(job.tsinstatus - job.tscreated)


	basic_url = "/admin/simhomes/%s/%s" % (xtor, name)
	repo_simoutput = repo_url(SIM, Manager.get_simid(xtor,name))

	def myurl(sel=selected_file):
		if sel is None:
			return basic_url
		else:
			return "%s?selected=%s" % (basic_url, sel)

	# create homedir file list
	files = []
	viewer_type = None
	for f in os.listdir(fileloc):
		fpath = os.path.join(fileloc, f)
		if os.path.isfile(fpath):
			files.append(f)
		if f==selected_file:
			if any(f.endswith(s) 
				for s in ('.txt', '.ini')):
				viewer_type='text'
				with open(fpath, 'r') as fs:
					viewer_content=fs.read()
			elif any(f.endswith(s) 
				for s in ('.jpg', '.png')):
				viewer_type='image'
			elif f.endswith('.json'):
				viewer_type = 'text'
				with open(fpath, 'r') as fs:
					unformatted=fs.read()
					try:
						viewer_content = json.dumps(json.loads(unformatted), indent=4, sort_keys=True)
					except:
						viewer_content = unformatted
			else:
				viewer_type='binary'
	files.sort()

	# return view
	refresh_page = job.state!='PASSIVE'
	thispage = myurl()
	return locals()


@app.route('/')
@view("monitor_table.html")
@AAA.logged_in
def index_html():
	refresh_page = True
	thispage = "/admin"
	return locals()


@app.route("/mainpage.css")
def get_css():
	return static_file("mainpage.css", root=gui_file_path())


@app.post("/run_simulation")
@view("job_table.html")
@AAA.logged_in
def submit_nsd():
	nsdid = request.forms.nsdid
	try:
		try:
			sim = api.create_simulation(nsdid)
		except:
			pass
		refresh_page = False
		thispage = "/admin/jobs.html"
		return locals()
	except ValueError as e:
		loggging.debug("In restapi.post_simulation", exc_info=1)
		raise HTTPError(status=403, body="The provided NSD id was not legal")
	except:
		logging.debug("In restapi.post_simulation", exc_info=1)
		raise HTTPError(status=500, body="An unknown error has occurred.")


@app.route("/nsd_table.html")
@view("nsd_table.html")
@AAA.logged_in
def show_nsd_table():
	refresh_page = True
	thispage = "/admin/nsd_table.html"
	return locals()

@app.route("/vectorl_table.html")
@view("vectorl_table.html")
@AAA.logged_in
def show_nsd_table():
	refresh_page = True
	thispage = "/admin/nsd_table.html"
	return locals()

@app.post("/run_vectorl")
@view("vectorl_results.html")
@AAA.logged_in
def process_vectorl():
	vectorl_id = request.forms.vectorl_id
	runit = 'run' in request.forms
	
	result = api.process_vectorl(vectorl_id, runit)
	output = json.dumps(result, indent=2)
		
	refresh_page = False
	return locals()


@app.get('/users.html')
@view('users.html')
@AAA.logged_in
def show_users():
	refresh_page = False
	thispage = "/admin/users.html"
	return locals()

@app.get('/create_user.html')
@view('create_user.html')
@AAA.logged_in
def create_user_dialog():
	username = request.query.get('username', '')
	is_admin = request.query.get('is-admin', False)
	return locals()

@app.get('/change_pass.html')
@view('change_pass.html')
@AAA.logged_in
def change_pass_dialog():
	username=request.query.get('username')
	return locals()

@app.get('/delete_user.html')
@view('delete_user.html')
@AAA.logged_in
def delete_user_dialog():
	username = request.query.get('username')
	return locals()

@app.post('/user_create')
@AAA.logged_in
def action_user_create():
	username = request.forms['new-username']
	password = request.forms['new-password']
	check_password = request.forms['check-password']
	is_admin = 'is-admin' in request.forms and request.forms['is-admin']=="yes"

	if password != check_password:
		return show_alert("Failed to create user", 
			"The passwords did not match", 
			"/admin/create_user.html?username=%s%s" % 
				(username,  "&is-admin=yes" if is_admin else ""))


	try:
		user = User(username, password, is_admin)
		api.create_user(user)
	except ConstraintViolation as e:
		logging.info("User creation failed because of bad username '%s'", username, exc_info=1)
		return show_alert("Failed to create user",
			"The user name '%s' is not valid. </p><p>"
			"User names must begin with a letter and <br/>"
			"have up to 24 characters. The first character must be a latin letter <br/>"
			"and the rest can be letters, numbers, underscore, dash or @" % username,
			"/admin/create_user.html"
			)
	except Exception as e:
		logging.exception("Manager failed to create user")
		return show_alert("Failed to create user",
			"The server encountered an internal error",
			"/admin/users.html"
			)

	redirect('/admin/users.html')


@app.post('/user_change_pass')
@AAA.logged_in
def action_change_pass():
	username = request.forms.username
	new_password = request.forms['new-password']
	check_password = request.forms['check-password']

	if not AAA.current_user_is_admin():
		old_password = request.forms['old-password']
		if not api.verify_password(AAA.create_user(), old_password):
			return show_alert("Operation failed",
				"Old password could not be verified",
				"/admin/change_pass.html?username=%s" % username)

	if new_password != check_password:
		return show_alert("Operation failed",
			"The new password did not check, retype it.",
			"/admin/change_pass.html?username=%s" % username)

	try:
		api.change_user_password(username, new_password)
	except api.Unauthorized:
		return show_alert("Operation failed",
			"You do not have permission to perform this operation",
			"/admin/users.html")

	redirect('/admin/users.html')

@app.get('/user_change_admin')
@AAA.logged_in
def action_change_admin():
	username = request.query.username
	is_admin = bool(int(request.query.is_admin))
	api.change_admin_status(username, is_admin)
	redirect('/admin/users.html')

@app.post('/user_delete')
@AAA.logged_in
def action_user_delete():
	username = request.forms.username
	api.delete_user(username)	
	redirect('/admin/users.html')


@view("alert.html")
def show_alert(title, message, link):
	'''This can be used in actions to show an alert.'''
	return locals()

@app.get("/acl.html")
@view("acl.html")
@AAA.logged_in
def show_acl():
	# compute the tree of entities
	from models.aaa import EClass

	ectree = []

	def visit(eclass, level):
		ectree.append((level, eclass))
		for ec in eclass.subclasses:
			visit(ec, level+1)

	for eclass in EClass.by_name.values():
		if not eclass.superclass: visit(eclass,0)

	return locals()



@app.error(400)
@app.error(500)
@view('generror.html')
def show_generic_error(e):
	return locals()


