
from models.aaa import *


def test_named():
	a = Named('a')
	b = Named('b')
	c = Named('c')
	d = Named('d')

	b <<= a
	d <<= c

	assert not c in a.implies
	c <<= b
	assert c in a.implies
	assert d in a.implies

