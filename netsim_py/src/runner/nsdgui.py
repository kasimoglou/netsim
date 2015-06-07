from runner.config import nsdEdit_file_path
import sys
import logging, os
import bottle
import os.path
import urllib.request 

from bottle import run, route, view, static_file, post, request

app = bottle.Bottle()

@app.route('/bower_components/<fname:path>')
def get_libraries(fname):
    raise static_file(fname, root=(nsdEdit_file_path() + '/bower_components'))

@app.route('/<fname:path>')
def index(fname):
    return static_file(fname, root=(nsdEdit_file_path() + '/dist'))

@app.route('/main.css')
def get_css():
    return static_file(fname, root=(nsdEdit_file_path() + '/dist/styles'))

