
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
	('~',np.invert, 3, ~3),
	('~',np.invert, True, False)
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


#
#  Constants for synthesizing expressions
#

_0 = Literal(0)
_1 = Literal(1)
_2 = Literal(2)
_3 = Literal(3)
_4 = Literal(4)
_5 = Literal(5)
_6 = Literal(6)
_7 = Literal(7)
_8 = Literal(8)
_9 = Literal(9)

_m1 = Literal(-1)
_m2 = Literal(-2)
_m3 = Literal(-3)
_m4 = Literal(-4)
_m5 = Literal(-5)

xvar = DummyVar(2)
yvar = DummyVar(3)

x1 = VarRef(xvar)
x2 = VarRef(xvar)
y = VarRef(yvar)


@pytest.mark.parametrize("p,q,D",[
	(_3, _5, 2),
	(_2 + _3,_5, 0),
	(_3,-_5, -8),
	(x1+_2, x2+_5 , 3),
	(x1,x1, 0),
	(x1-(_5+x2), _1-_1 , 5),
	(x1 - x2 + x2, x1, 0),
	(x1*y, x2*y, 0),
	(_2*x1-IF(y>_2, x1+y, _3), _2*x2-IF(y>_2, x1+y, _3), 0),
	(x1, _5, None)
])
def test_diff(p, q, D):
	assert Diff(p,q) == D
	if D is not None:
		assert Diff(q,p) == -D
	else:
		assert Diff(q,p) is None
 
def test_diff_funcs():
	assert Additive( (_1-_1)-(x1-(_5+x2)) ) == (5,None)
	assert Equal(_2*x1/IF(y>_2, x2+y, _3), _2*x2/IF(y>_2, x1+y, _3))


@pytest.mark.parametrize("index, shape, rshape, tindex",
	[
	((_1,_2,_3), (5,5,5),
		tuple(), (1,2,3)),

	(tuple([...]), (3,3,3),
		(3,3,3), (slice(0,3,1), slice(0,3,1), slice(0,3,1))),

	(tuple([_1,slice(_1,None,_m1)]), (3,4,4,1) ,
		(2, 4, 1), (1, slice(1,-5,-1), slice(0,4,1), slice(0,1,1))),

	(tuple([_1,slice(_1,None,_m1),...]), (3,4,4,1),
	 	(2, 4, 1), (1, slice(1,-5,-1), slice(0,4,1), slice(0,1,1))),

	(tuple([_1,slice(_1,None,_m1),...,slice(None,None,None)]), (3,4,4,1),
		(2, 4, 1), (1, slice(1,-5,-1), slice(0,4,1), slice(0,1,1))),

	(tuple([_1,slice(_1,None,_m1),...,slice(None,None,None),slice(None,None,None)]), (3,4,4,1),
		(2, 4, 1), (1, slice(1,-5,-1), slice(0,4,1), slice(0,1,1))),

	(tuple([_1,slice(_1,None,_m1),...,slice(None,None,None),slice(None,None,None)]), (3,4,4,1),
		(2, 4, 1), (1, slice(1,-5,-1), slice(0,4,1), slice(0,1,1))),

	(tuple([...,_1,slice(_1,None,_m1),slice(None,None,None),slice(None,None,None)]), (3,4,4,1),
		(2, 4, 1), (1, slice(1,-5,-1), slice(0,4,1), slice(0,1,1))),

	(tuple([...,_1,slice(_1,None,-_1),slice(None,None,None),slice(None,None,None)]), (3,4,4,1),
		(2, 4, 1), (1, slice(1,-5,-1), slice(0,4,1), slice(0,1,1))),

	(tuple([_3]), (4,), tuple(), (3,))

	])
def test_const_indexer(index, shape, rshape, tindex):
	I = Indexer(index, shape)
	assert I.shape == rshape
	assert I.const
	assert I.impl()() == tindex


@pytest.mark.parametrize("index, shape",
	[
	((_1,_2,_3), (5,5,2)),

	(tuple([...,_4]), (3,3,3)),	

	(tuple([_1,slice(_5,None,_m1)]), (3,2,4,1) ),

	(tuple([_4,slice(_1,None,_m1),...]), (3,4,4,1)),

	(tuple([_1,slice(_1,None,_m1),...,slice(None,None,None)]), (3,4)),

	(tuple([_1,slice(_1,None,_m1),...,slice(None,None,None),slice(None,None,None)]), (3,)),

	(tuple([_1,slice(_1,None,_m1),...,slice(None,None,None),slice(None,None,None)]), tuple()),

	(tuple([...,_1,slice(_1,None,_m1),slice(None,None,None),slice(None,None,None)]), (3,4,4)),

	(tuple([...,_1,slice(_1,None,-_1),slice(None,None,None),slice(None,None,None)]), (3,1)),

	(tuple([_3]), (2,)),

	(tuple([Literal(1.0)]), (2,)),

	(tuple([Literal(False)]), (2,)),

	])
def test_bad_const_indexer(index, shape):
	with pytest.raises(ValueError):
		Indexer(index, shape)



@pytest.mark.parametrize("index, shape, rshape, tindex",[
	( (x1,), (1,2),
		(2,), [((1,), (1,slice(0,2,1)))]),

	( (x1,slice(x1+_3,x2-_1,-_1)), (3,5),
		(4,), [((1,4,0,-1), (1,slice(4,0,-1)))])
])
def test_var_indexer(index, shape, rshape, tindex):
	I = Indexer(index, shape)
	assert I.shape == rshape
	assert not I.const
	impl = I.impl()
	for v, z in tindex:
		assert impl(*v) == z


def test_index():
	arr = Concat(* (Array(Literal(i)) for i in range(1,5)))	
	A = Array(arr,arr,arr)

	assert A.shape == (3,4)	
	A1 = A[_1,:]
	assert A1.shape == (4,)
	assert A1.const
	assert not A1.lvalue
	assert A1.type is INT
	assert all(A1.value == np.array([1,2,3,4]))


