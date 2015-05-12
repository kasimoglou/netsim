
import pytest
from vectorl.expr import *
import numpy as np


def test_broadcast():
	assert compute_broadcast_shape({(1,), (5,)})==(5,)
	assert compute_broadcast_shape({(2,), (5,)}) is None

	assert compute_broadcast_shape({(1,2,3), (2,2,1)})==(2,2,3)
	assert compute_broadcast_shape({tuple(), (3,)})==(3,)
	assert compute_broadcast_shape({tuple(), (5,), (3,4,5)})==(3,4,5)
	assert compute_broadcast_shape({tuple(), (3,), (1,)})==(3,)

def test_UFUNC():
	class Foo:
		def __init__(self, type):
			self.type = type

	a = UFUNC('+', np.add)

	assert a[0] == '+'
	assert a[1]
