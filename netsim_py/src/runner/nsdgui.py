import sys
import logging, os
import bottle
import os.path
import urllib.request 

from bottle import run, route, view, static_file, post, request

from runner.config import nsdEdit_file_path
import runner.AAA as AAA


logger = logging.getLogger("GUI")

app = bottle.Bottle()

@app.route('/bower_components/<fname:path>')
def get_libraries(fname):
    raise static_file(fname, root=(nsdEdit_file_path() + '/bower_components'))



@app.route('/<fname:path>')
def index(fname):
    if fname.startswith("html/index"):
        #
        # We have angular which uses the URL fragment to denote internal
        # pages.
        #

        # try to collect user, plan and project info before the fragment
        dpcm_user = request.query.user
        project_id = request.query.project_id
        plan_id = request.query.plan_id

        # save into the sesssion what is to be saved
        if dpcm_user or project_id or plan_id:
            if dpcm_user:
                AAA.set_dpcm_user(dpcm_user)
            if project_id:
                AAA.session_set('project_id', project_id)           
            if plan_id:
                AAA.session_set('plan_id', plan_id)
            logger.info("Main page loaded, current user=%s, project=%s, plan=%s", dpcm_user, project_id, plan_id)


    return static_file(fname, root=(nsdEdit_file_path() + '/dist'))

@app.route('/main.css')
def get_css():
    return static_file(fname, root=(nsdEdit_file_path() + '/dist/styles'))

