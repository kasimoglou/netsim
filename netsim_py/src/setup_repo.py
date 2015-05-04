'''
Created on Mar 23, 2015

Create and use a copy of the DPCM repository to a local couchdb server.

@author: vsam
'''

import argparse, sys
from runner.config import cfg, configure
from runner.dpcmrepo import ProjectRepository

LOCAL="http://127.0.0.1:5984/"
REMOTE="http://213.172.45.30:5984/"


def replicate(server, src, dst):
	for dbname in ('pt_repository', 'simulator'):
		source = src+dbname
		destination = dst+dbname

		if destination in server:
			print('Deleting old destination:', destination)
			server.delete(destination)

		print('Creating destination:', destination)
		server.create(destination)

		print('Replicating',source,'to',destination)
		server.replicate(source, destination)


def pull(server):
	replicate(server, REMOTE+'dpcm_', 'remote_')

def clone(server):
	replicate(server, 'remote_', 'dpcm_')

def prepare(server):
	print('Preparing project repository at',REMOTE)
	from models.project_repo import MODELS
	server.create_models(MODELS)


def main():

	global LOCAL, REMOTE

	#configure('sim_runner')
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
	''')
	parser.add_argument("operation",  help="Select the operation.",
						choices=['pull','clone', 'prepare'])

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
	elif args.operation=='clone':
		server = ProjectRepository(args.local)
		clone(server)
	elif args.operation=='prepare':
		server = ProjectRepository(args.remote)
		prepare(server)
	else:
		print('An invalid operation was chosen!')
		sys.exit(1)


if __name__=='__main__':
    main()
    
