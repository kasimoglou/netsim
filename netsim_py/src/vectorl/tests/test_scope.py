
import pytest
from vectorl.parser import *


def test_scope():
    s1 = Scope()
    s2 = Scope(s1)
    s3 = Scope()
    s1.bind('foo',s3)
    s3.bind('bar',1)

    assert s2[('foo','bar')]==1 

def test_lookup():
	S = Scope()
	S.bind('a', 1)

	# Bound value in 
	assert 'a' in S
	assert 'b' not in S
	assert S.lookup('a')==1

	# on failure, return None
	assert S.lookup('b')==None

	S2 = Scope(S)
	# superscope access
	assert not S2.binds('a')
	assert S2.lookup('a')==1
	assert S2.lookup('b')==None

	S2.bind('a', 2)
	# superscope overruled
	assert S2.binds('a')
	assert S2.lookup('a')==2

def test_bind():
	S = Scope()
	S.bind('a',1)

	# Error on key redef
	with pytest.raises(KeyError):
		S.bind('a',2)
	assert S.binds('a')
	assert S.lookup('a')==1

	# use the force 
	S.bind('a',2, force=True)
	assert S.binds('a')
	assert S.lookup('a')==2

	# use the force on a new identifier
	S.bind('b',3, force=True)
	assert S.binds('b')
	assert S.lookup('b')==3

	# bad key
	with pytest.raises(KeyError):
		S.bind(1,2)
	with pytest.raises(KeyError):
		S.bind('1',2)

	# bad value
	with pytest.raises(ValueError):
		S.bind('c', None)


def test_getitem():
	S = Scope()

	seq = {}
	# create a sequence of nested scopes
	oldS = S
	for a in "ABCDE":
		newS = Scope(oldS)
		seq[a] = newS
		oldS.bind(a, newS)
		oldS = newS

	assert S['A'] is seq['A']
	assert S['A','B']  is seq['B']
	assert S[('A','B')] is seq['B']
	assert S['A.B'] is seq['B']

	assert S['A.B','C'] is seq['C']






