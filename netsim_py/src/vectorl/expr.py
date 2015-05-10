#
# This is the VectorL python runtime engine.
# It is based on numpy
#

from collections import namedtuple
import numpy as np

#
# Types
#

class TYPEOPS:
	def __init__(self, name, pytype, make, rank):
		self.name = name
		self.pytype = pytype
		self.make = make
		self.dtype = make([0]).dtype #numpy type
		self.rank = rank

BOOL = TYPEOPS('bool', bool, np.bool_, 1)
INT = TYPEOPS('int', int, np.int_, 2)
REAL = TYPEOPS('real', float, np.float_, 3)
TIME = TYPEOPS('time', float, np.float_, 4)

TYPES = [BOOL, INT, REAL, TIME]

# This is used to manipulate data!
OBJ = TYPEOPS('object', object, lambda x: np.array(x, dtype=object), 5)

TYPE = {t.name:t for t in TYPES}
DTYPE = {t.dtype : t  for t in TYPES}
RANK = {t.rank: t for t in TYPES}

def promoted_type(*types):
	assert types
	return RANK[max(t.rank for t in types)]


#
# Expression tree. This is used for inference.
#


# leaf nodes


class VarRef:
    def __init__(self, var):
    	self.var=var
    	self.type = var.type

    const = False
    lvalue = True

    @property 
    def shape(self): return self.var.initval.shape


class Constant:
    def __init__(self, val, type):
    	self.value = val
    	self.type = type

    @property 
    def shape(self): return self.value.shape

    const = True
    lvalue = False


# internal nodes

def broadcast_shape(*args):
	'''
	Return the broadcast size for arguments, having attribute 'shape'
	'''
	if not args: return tuple()
	sizes = {a.shape for a in args}
	return compute_broadcast_shape(sizes)

def prepad(tup, l):
	'''
	Prepad a tuple tup to length l, with 1's
	'''
	return (1,)*(l-len(tup))+tup

def broadcastable(lhs, rhs):
	'''return true if the rhs shape is broadcastable to
	the lhs.
	'''
	if len(lhs)<len(rhs):
		return False
	return all(x==y or y==1 for x,y in zip(lhs, rhs))


def compute_broadcast_shape(shapes):
	'''
	Compute a broadcast size where all shapes in 'shapes'
	(a sequence) can be broadcast. Return None if it is not
	possible.
	'''
	sizes = list(shapes)
	l = max(len(s) for s in sizes)
	# prepend ones to extend sizes
	esizes = [prepad(s,l) for s in sizes]
	# compute point-wise max of esizes
	L = tuple(max(*t) for t in zip(*esizes))

	# check if all esizes are broadcastable
	if all(broadcastable(L, s) for s in esizes):
		return L
	else:
		return None
	


class Operator:
	def __init__(self, op, *args, type, size, lvalue, const):
		self.op = op
		self.args = args
		self.type = type
		self.shape = size
		self.lvalue = lvalue
		self.const = const


#
# Operator implementations
#


#
# Operator description
#

# computing result type

def std_result_type(*args):
	'''
	Return the result type applying standard C++ conversions.
	'''
	return DTYPE[np.result_type(*[a.type.dtype for a in args])]

def given_type(n):
	'''Return the type of an argument'''
	def test(*args):
		return args[n].type
	return test

# computing constness

def all_const(*args):
	''' Return true iff all args are const '''
	return all(a.const for a in args)

def none_const(*args):
	''' Return true. '''
	return True

def mask_const(* flags):
	''' Return a function which checks constness of a sequence
	of arguments, using a boolean mask. Where the mask is True,
	the argument must be constant.
	'''
	def test(* args):
		return all( ((not f) or a.const) for f,a in zip(flags, args) )
	return test

# Helper routine for describing numpy UFUNC operators

def UFUNC(name, uf):
	impl = uf
	arity = uf.nin

	def rtype(*args):
		s = np.result_type(*[a.type.dtype for a in args])
		s = s.char * len(args)

		tt = ''.join(s) + "->"

		for m in uf.types:
			if m.startswith(tt):
				rt=m[:len(tt)]
				return DTYPE[dtype(rt)]
		return None

	def rsize(*args):
		return broadcast_shape(*args)
	return (name, uf, arity, rtype, rsize, all_const)

# unary
OP1_TABLE=[
	('+', None, 1, lambda arg: arg.type, lambda arg: arg.shape, all_const),
	UFUNC('-', np.negative),
	UFUNC('~', np.invert),
	UFUNC('!', np.logical_not)
]

# binary 
OP2_TABLE=[
	# name,   operator,		impl, 		arity,	result_type,	result_size,	result_const
	UFUNC('+', np.add),
	UFUNC('-', np.subtract),
	UFUNC('*', np.multiply),
	UFUNC('/', np.divide),
	UFUNC('%', np.remainder),
	UFUNC('&', np.bitwise_and),
	UFUNC('|', np.bitwise_or),
	UFUNC('^', np.bitwise_xor),
	UFUNC('<<', np.left_shift),
	UFUNC('>>', np.right_shift),

	UFUNC('>', np.greater),
	UFUNC('>=', np.greater_equal),
	UFUNC('<', np.less),
	UFUNC('<=', np.less_equal),
	UFUNC('==', np.equal),
	UFUNC('!=', np.not_equal),

	UFUNC('&&', np.logical_and),
	UFUNC('||', np.logical_or)
]


#
# operator models
#

class OperatorModel:
	def __init__(self, operator, impl, arity, result_type, result_size, result_const, **kwargs):
		self.operator = operator 	# from the ast (e.g., '-', '!', etc)
		self.impl = impl 			# the executable function 

		self.arity = arity			# number of arguments (None: unbounded)
		self.result_type = result_type
		self.result_size = result_size
		self.result_const = result_const

OPERATOR = {}
OPERATOR['unary'] = { op[0] : OperatorModel(* op ) for op in OP1_TABLE }
OPERATOR['binary'] = { op[0] : OperatorModel(* op ) for op in OP2_TABLE }


# Five special operators: concat cast funcall cond index

class CastOperatorModel:
	def __init__(self, ctype):
		self.operator = ctype.name
		self.ctype = ctype
		self.arity = 1

	def impl(self, x):
		return self.ctype.dtype(x)

	def result_type(self, arg):
		return self.ctype

	def result_size(self, arg):
		return arg.shape

	def result_const(self, arg):
		return arg.const

OPERATOR['cast'] = { t.name: CastOperatorModel(t) for t in TYPES }


class ConcatOperatorModel:
	def __init__(self):
		self.operator = 'concat'
		self.arity = None

	@staticmethod
	def impl(*args):
		ndim = {a.ndim for a in args}
		if len(ndim)!=1:
			raise ValueError("all arguments must have the same dimension")
		ndim = ndim.pop()
		if ndim:
			return np.concatenate(*args)
		else:
			return np.array(*args)

	@staticmethod
	def result_size(*args):
		sizes = [a.shape for a in args]
		ndim = len(sizes[0])
		if any(len(s)!=ndim for s in sizes):
			return None
		if ndim==0:
			return (sum(sizes),)
		else:
			tsizes = {s[1:] for s in sizes}
			bsize = compute_broadcast_shape(tsizes)
			if bsize is None:
				return None
			ssize = sum(s[0] for s in sizes)
			return (ssize,)+bsize

	result_type = std_result_type

	result_const = all_const

OPERATOR['concat'] = ConcatOperatorModel()


# cond
class CondOperatorModel:
	def __init__(self):
		self.operator = 'cond'
		self.arity = 3

	impl = np.where

	def result_type(self, *args):	
		return std_result_type(args[1], args[2])

	result_size = broadcast_shape

	result_const = all_const

# funcall

# function calls do not refer to Vectorl functions but to
# 'builtin' functions (library, aggregate etc).



# index expressions

class IndexOperatorModel:
	pass


