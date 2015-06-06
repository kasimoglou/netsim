'''
Testing for utils.py

@author: vsam
'''

import pytest, os.path
from simgen.utils import *
from tempfile import mkdtemp
from shutil import rmtree

@pytest.fixture
def tempdir(request):
	d = mkdtemp(dir="/tmp", prefix="dpcm_unit_test_")
	cwd = os.getcwd()
	def fin():
		rmtree(d)
		os.chdir(cwd)
	request.addfinalizer(fin)
	os.chdir(d)
	return d

def assert_file_eq(path, contents):
	assert get_file(path)==contents


CONTENT = """\
Zavarakatranemia.
Ileos, Ileos"""

CONTENT2 = """\
Ouaga boom boom gi gaga ugigi gaga.
"""


def test_put_file(tempdir):
	put_file('foo',CONTENT)
	path = os.path.join(tempdir, 'foo')
	assert os.access(path, os.R_OK)
	assert_file_eq('foo', CONTENT)
	assert_file_eq(path, CONTENT)
	put_file('foo', CONTENT2)
	assert_file_eq(path, CONTENT2)

def test_put_new_file(tempdir):
	put_new_file('foo',CONTENT)
	with pytest.raises(IOError):
		put_new_file('foo',CONTENT)
	path = os.path.join(tempdir, 'foo')
	assert os.access(path, os.R_OK)
	assert_file_eq('foo', CONTENT)
	assert_file_eq(path, CONTENT)

def test_append_file(tempdir):
	put_file('foo',CONTENT)
	path = os.path.join(tempdir, 'foo')
	assert os.access(path, os.R_OK)
	assert_file_eq('foo', CONTENT)
	assert_file_eq(path, CONTENT)
	append_to_file('foo', CONTENT2)
	assert_file_eq(path, CONTENT+CONTENT2)


# Test that a function raising an exception 
# returns the exception
def func_raises():
	raise RuntimeError

def func_add(a,b):
	return a+b

def test_execute_function_exception(tempdir):
	with pytest.raises(RuntimeError):
		execute_function(tempdir, func_raises, 'test', True)

def test_execute_function_return_int(tempdir):
	ret = execute_function(tempdir, func_add, 'test', True, 12, 20)
	assert ret==32

class Concat:
	def __init__(self, val):
		self.val = val

def func_concat(*args):
	return Concat(''.join(args))

def test_execute_function_return_object(tempdir):
	ret = execute_function(tempdir, func_concat, 'test', True, 'abc','de', 'f')
	assert isinstance(ret, Concat)
	assert ret.val == 'abcdef'

def func_print():
	import sys
	print('this is stdout', flush=True)
	print('this is stderr', file=sys.stderr)

# Test redirection
def test_execute_function_redir(tempdir):
	ret = execute_function(tempdir, func_print, 'test', True)
	assert ret is None
	assert_file_eq('stdout.test.txt', 'this is stdout\n')
	assert_file_eq('stderr.test.txt', 'this is stderr\n')

	
@pytest.fixture(params=[
	['x','x','x'],
	['What a nice day', 'What!a nice day'],
	['x','x_1','x 1','x+1', 'x+1']
	])
def names(request):
	return request.param

def test_construct_legal_ids(names):

	nmap = construct_legal_ids(names)

	print("from: ",names)
	print("to: ", nmap)

	# all names are mapped
	assert set(names)==set(nmap.keys())

	# non-empty
	for n in nmap:
		assert nmap[n]

	# all mapped names are disjoint
	L = []
	for l in nmap.values():
		L += l
	assert len(set(L)) == len(L)






