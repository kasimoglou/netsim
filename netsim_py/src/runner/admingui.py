'''
Created on Mar 13, 2015

@author: vsam
'''


'''
Created on Mar 3, 2014

@author: vsam
'''

from runner.monitor import Manager
from runner.config import gui_file_path
#from runner.SimPreparator import *
from runner import api
import sys
import logging, os
import bottle
import os.path
import urllib.request 
import pycouchdb


from bottle import run, route, view, static_file, post, \
					request, HTTPError, redirect, abort
from threading import Thread

from runner import AAA


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
	AAA.logout()
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

	if AAA.login(user, password):
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

@app.route("/download_nsd.html")
@view("download_nsd.html")
@AAA.logged_in
def show_job_form():
	refresh_page = False
	thispage = "/admin/download_nsd.html"
	return locals()


@app.route("/nsd_simulations.html")
@view("nsd_simulations.html")
@AAA.logged_in
def show_nsd_simulations():
	refresh_page = False
	thispage = "/admin/nsd_simulations.html"
	return locals()


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
def show_job_form():
	refresh_page = True
	thispage = "/admin/nsd_table.html"
	return locals()

@app.error(400)
@app.error(500)
@view('generror.html')
def show_generic_error(e):
	return locals()


