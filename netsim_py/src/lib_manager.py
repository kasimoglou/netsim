
'''
Created on Mar 23, 2015

Project repository library management operations

@author: vsam
'''

import argparse, sys, json
from os.path import basename, isdir, join

from runner.config import cfg, configure
from runner.dpcmrepo import ProjectRepository, NotFound
from models.project_repo import MODELS, NS_COMPONENT

repo = None
libdb = None


def list_files():
	for obj in libdb.all():
		fname = obj['key']
		if '/' in fname: continue
		ftype = obj['doc']['type']
		print("%-32s  %s" % (fname, ftype))


def dump_all(fdir):
	if not isdir(fdir):
		print("%s is not a directory", fdir)
		sys.exit(1)
	for obj in libdb.all():
		fname = obj['key']
		if '/' in fname: continue
		doc = obj['doc']
		del doc['_id']
		del doc['_rev']
		fpath = join(fdir, fname)
		print(fpath)
		with open(fpath, "w") as f:
			f.write(json.dumps(doc, indent="  "))



def unwrap_list(L):
	if L is not None:
		for f in L:
			if isinstance(f, list):
				yield from unwrap_list(f)
			else:
				yield f


def view_files(fnames, attach):
	for fname in unwrap_list(fnames):
		if attach is None:
			view_file(fname)
		else:
			view_attachment(fname, attach)


def get_files(fnames, attach):
	for fname in unwrap_list(fnames):
		if attach is None:
			get_file(fname)
		else:
			get_attachment(fname, attach)

def put_files(fnames, attach):
	for fname in unwrap_list(fnames):
		if attach is None:
			put_file(fname)
		else:
			put_attachment(fname, attach)

def GET_attachment(fname, attach):
	print("Getting attachment %s from %s"%(fname, attach))
	doc = libdb.get(attach)
	content = libdb.get_attachment(doc, fname)
	return content

def get_attachment(fname, attach):
	content = GET_attachment(fname, attach)
	with open(fname,'w') as f:
		f.write(content.decode())

def view_attachment(fname, attach):
	content = GET_attachment(fname, attach)
	print(content.decode('utf8'))


def GET_file(fname):
	obj = libdb.get(fname)
	del obj['_id']
	del obj['_rev']
	txt = json.dumps(obj, indent="    ")
	return txt

def get_file(fname):
	txt = GET_file(fname)
	with open(fname, "w") as f:
		f.write(txt)

def view_file(fname):
	txt = GET_file(fname)
	print(txt)	

def put_attachment(fname, attach):
	print("Putting attachment %s to %s"%(fname, attach))
	with open(fname, 'rb') as f:
		content = f.read()
	doc = libdb.get(attach)
	libdb.put_attachment(doc, content, filename=basename(fname), content_type="text/plain")


def put_file(fname):
	with open(fname, 'r') as f:
		obj = json.loads(f.read())
	oid = basename(fname)
	try:
		oldobj = libdb.get(oid)
		obj['_rev'] = oldobj['_rev']
	except NotFound:
		pass
	obj['_id'] = oid
	libdb.save(obj)


def main():

	configure('sim_runner')

	parser = argparse.ArgumentParser(description='''
	This program manages the simulation library in the DPCM project repository.
	''')


	parser.add_argument("--repo", '-r',
	    help="The url to the remote couchdb installation of the DPCM repository.\
	     The default is taken from the config file (%s)" % cfg.project_repository, 
	    default=cfg.project_repository)


	parser.add_argument("--attach", '-a',
		help="List the files in the library"
		)


	parser.add_argument("--ls", '-l',
		help="List the files in the library",
		action="store_true"
		)

	parser.add_argument("--text",'-x',
		help="Load/store raw file",
		action="store_true")

	parser.add_argument("--put", '-p', nargs="+",
		help="Put the named files in the library",
		action="append"
		)

	parser.add_argument("--get", '-g', nargs="+",
		help="Get the named files from the library",
		action="append"
		)

	parser.add_argument("--view", '-v', nargs="+",
		help="View the named files from the library",
		action="append"
		)

	parser.add_argument("--dump", '-d', 
		help="Save all files in the given directory."
		)

	args = parser.parse_args()

	print("Repository:", args.repo)

	global repo, libdb
	repo = ProjectRepository(cfg.project_repository)
	libdb = repo.db_of(NS_COMPONENT)

	if args.ls:
		list_files()
	elif args.get is not None:
		get_files(args.get, args.attach)
	elif args.put is not None:
		put_files(args.put, args.attach)
	elif args.dump is not None:
		dump_all(args.dump)
	elif args.view is not None:
		view_files(args.view, args.attach)



if __name__=='__main__':
    main()
    
