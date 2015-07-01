'''
Created on Mar 23, 2015

Project repository management operations

@author: vsam
'''

import argparse, sys
from runner.config import cfg, configure
from runner.dpcmrepo import ProjectRepository
from models.project_repo import MODELS, SIM

LOCAL="http://127.0.0.1:5984/"
REMOTE="http://213.172.45.30:5984/"

local = None
remote = None



def replicate(server, src):

	for dbname in ('dpcm_pt_repository', 
			'dpcm_simulator',
			'castalia_node_library', 
			'dpcm_integration_repo'):
		source = src+dbname
		destination = dbname

		if dbname in server:
			print('Deleting old destination:', destination)
			server.delete(destination)

		print('Creating destination:', destination)
		server.create(destination)

		print('Replicating',source,'to',destination)
		server.replicate(source, destination)


def pull(server):
	replicate(server, REMOTE)



def prepare(server):
	print('Preparing project repository at',REMOTE)
	from models.project_repo import MODELS
	server.create_models(MODELS)




def view_model(server, model):
	# read the model
	entity = model.entity
	fields = [f.name for f in entity.fields]
	fields.sort()

	allView = [v for v in model.views if v.name=='all'][0]

	# read in the data
	db = server.database(cfg[entity.database.name])
	query = db.query(allView.resource)

	data = [] 							# data array
	fsize = [len(f) for f in fields]    # field width
	for obj in query:
		row = [str(obj['value'].get(f,None)) for f in fields]
		data.append(row)
		# update field sizes
		rsize = [len(s) for s in row]
		fsize = [max(x) for x in zip(fsize,rsize)]


	fpat = ['%%%ds' % w for w in fsize]
	def print_row(X):
		P = [pat % x for pat, x in zip(fpat, X)]
		print(*P,sep="|")

	# display header
	lsize = sum(fsize)+len(fsize)
	print('='*lsize)
	print("Entity: ", entity.name)
	print('-'*lsize)
	# print header
	print_row(fields)
	print('-'*lsize)
	for row in data:
		print_row(row)		
	print('='*lsize)
	print()
	print()


def view(server):
	print('Examining project repository at',REMOTE)
	for model in MODELS:
		view_model(server, model)


def cleanup(server, args):
	print('Cleaning up project repository at',LOCAL)
	if not args:
		args = ['test']
	for exc in args:
		print("Removing simulations for executor", exc)
		prefix = "SIMOUTPUT:%s:" % exc
		db = server.db_of(SIM)
		stale = []
		for obj in db.all():
			if obj['id'].startswith(prefix):
				stale.append(obj['doc'])
		db.delete_bulk(stale)



def main():

	global LOCAL, REMOTE

	configure('sim_runner')
	#REMOTE = cfg.project_repository

	parser = argparse.ArgumentParser(description='''
	This program will partially copy the DPCM project repository to a private
	couchdb server and create test copies to be used by test code.

	There are two operations:
	pull  -- copy from the DPCM couchdb the dpcm_pt_repository and dpcm_simulator
	         databases to local copies, renamed remote_pt_repository and remote_simulator.

	clone -- copy locally the 'remote_pt_repository' and 'remote_simulator' to
	         'dpcm_pt_repository' and 'dpcm_simulator' respectively.

	prepare -- prepare the remote server for the network simulator. This basically loads
	       some view definitions and other design docs into the remote server.

	cleanup [exec] -- clean up the local server: remove all SIMOUTPUT objects with 
	     the given executor ('test' executor by default).
	''')
	parser.add_argument("operation",  help="Select the operation.", 
						choices=['pull','clone', 'prepare', 'view', 'cleanup'])

	parser.add_argument("args", 
		help="Arguments to the commands (see description)",
		nargs="*")

	parser.add_argument("--remote", '-r',
	                    help="The url to the remote couchdb installation of the DPCM repository.\
	                     The default is taken from the config file (%s)" % REMOTE, 
	                    default=REMOTE)

	parser.add_argument("--local", '-l', 
	                    help="The url to the local couchdb. The default is http://127.0.0.1:5984/",
	                    default=LOCAL)

	args = parser.parse_args()

	LOCAL = args.local
	REMOTE = args.remote


	if args.operation=='pull':
		server = ProjectRepository(args.local)
		pull(server)
	elif args.operation=='prepare':
		server = ProjectRepository(args.remote)
		prepare(server)
	elif args.operation=='view':
		server = ProjectRepository(args.remote)
		view(server)
	elif args.operation=='cleanup':
		server = ProjectRepository(args.local)
		cleanup(server, args.args)
	else:
		print('An invalid operation was chosen!')
		sys.exit(1)


if __name__=='__main__':
    main()
    
