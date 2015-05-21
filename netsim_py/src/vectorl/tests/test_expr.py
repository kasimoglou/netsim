
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



@pytest.mark.parametrize('value, type',
	[
	(0, INT),
	(0.0, REAL),
	(False, BOOL)
	])
def test_literal(value, type):
	l = Literal(value)
	assert l.type is type
	assert l.const
	assert not l.lvalue
	assert l.value ==value
	assert l.shape == tuple()

class DummyVar:
	def __init__(self, ival):
		if isinstance(ival, ExprNode):
			self.initval = ival
		else:
			self.initval = Literal(ival)
		self.type = self.initval.type

def test_varref():
	x = VarRef(DummyVar(2))
	assert x.type is INT
	assert not x.const
	assert x.lvalue

	y = x+Literal(1)
	assert y.type is INT
	assert not y.const
	assert not y.lvalue

def test_binary_simple():
	x= Literal(1)+Literal(1)
	assert x.type is INT
	assert x.const
	assert x.op == '+'
	assert x.operator_arity() == 2

	x = VarRef(DummyVar(1)) * Literal(1.0)
	assert x.type is REAL
	assert not x.const
	assert not x.lvalue
	assert x.op == '*'
	assert x.operator_arity() == 2

	z=-x
	assert z.type is REAL
	assert not z.const
	assert not z.lvalue
	assert z.op == '-'
	assert z.operator_arity() == 1

	a = Parameter('a', type=INT)
	x = a+Literal(1)
	assert x.type is INT
	assert x.shape is None
	assert x.const is None
	assert not x.lvalue

def test_type_promo():
	assert (Literal(1)+Literal(0.0)).type is REAL
	assert (Literal(True)+Literal(0.0)).type is REAL
	assert (Literal(True)+Literal(0)).type is INT
	assert (Literal(True)+Literal(False)).type is BOOL

	assert (Literal(True)+Literal(True)).value == True

@pytest.mark.parametrize("op,ufunc, val,res",[
	('-',np.negative, 3, -3),
	('-',np.negative, 3.0, -3.0),
	('-',np.negative, True, False),
	('-',np.invert, 3, ~3),
	('-',np.invert, True, False)
	])
def test_unary_operator(op, ufunc, val, res):
	expr = UFuncOperator(op, ufunc, Literal(val))
	assert expr.const
	assert expr.value == res

@pytest.mark.parametrize("op,ufunc, a, b, res",[
	('+', np.add, 2., 3, 5),
	('*', np.multiply, 2., False, 0),
	('<<', np.left_shift, -1, 1, -2),
	('<<', np.left_shift, 1, 10, 1024),
	('>>', np.right_shift, 1, 6, 0),
	('>>', np.right_shift, 1000, 6, 15)
	])
def test_binary_operator(op, ufunc, a, b, res):
	expr = UFuncOperator(op, ufunc, Literal(a), Literal(b))
	assert expr.const
	assert expr.value == res

def test_casts():
	assert Literal(1.1).cast(BOOL).value is np.bool_(1)
	assert Literal(1.1).cast(INT).value == 1
	assert Literal(1.1).cast(REAL).value == 1.1
	assert Literal(1.1).cast(TIME).value == 1.1

	assert isinstance(Literal(1).cast(INT), CastOperator)
	assert isinstance(Literal(1).cast_if_needed(INT), Literal)

def test_concat():
	arr = Concat(* (Array(Literal(i)) for i in range(1,5)))	
	assert arr.shape == (4,)
	assert np.all(arr.value == np.array([1,2,3,4]))

	with pytest.raises(ValueError):
		Concat(Literal(1), Array(Literal(2))).value.shape == (1,)

	assert Concat(arr,arr).shape == (8,)
	assert Concat(arr, Array(Literal(1))).shape == (5,)

	a2 = Array(arr, arr, arr)
	assert a2.shape == (3,4)
	assert Concat(a2, a2, a2).shape == (9,4)


def test_diff():
	xvar = DummyVar(2)
	yvar = DummyVar(3)

	x1 = VarRef(xvar)
	x2 = VarRef(xvar)
	y = VarRef(yvar)

	_1 = Literal(1)
	_2 = Literal(2)
	_3 = Literal(3)
	_5 = Literal(5)

	assert Diff(x1+_2, x2+_5)==3
	assert Diff(x1,x1)==0
	assert Additive( (_1-_1)-(x1-(_5+x2)) ) == (5,None)
	assert Diff(x1-(_5+x2), _1-_1)==5
	assert Diff(x1 - x2 + x2, x1 )==0

	assert Diff(x1*y, x2*y)==0

	assert Equal(_2*x1/IF(y>_2, x1+y, _3), _2*x2/IF(y>_2, x1+y, _3))
	assert Diff(_2*x1-IF(y>_2, x1+y, _3), _2*x2-IF(y>_2, x1+y, _3))==0



def test_index():
	arr = Concat(* (Array(Literal(i)) for i in range(1,5)))	
	A = Array(arr,arr,arr)

	assert A.shape == (3,4)	

	assert A[Literal(1),:].shape == (4,)

