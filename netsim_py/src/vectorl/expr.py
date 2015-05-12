#
# This is part of the VectorL python runtime engine.
# This is the part where computations are described.
# It is based on numpy.
#

from collections import namedtuple
import numpy as np
from models.mf import *

#
# Types: We use types declared by numpy.
#  
#

class TypeInfo:
    '''
    Model for a VectorL type.
    '''
    def __init__(self, name, pytype, make, rank):
        self.name = name
        self.pytype = pytype
        self.make = make
        self.dtype = make([0]).dtype #numpy type
        self.rank=rank

    @staticmethod
    def forLiteral(x):
        '''
        Find the type for a literal
        '''
        for T in TYPES:
            if isinstance(x, T.pytype): return T
        return Type.OBJ

    @staticmethod
    def forType(t):
        return TypeInfo.bytype[t]

    @staticmethod
    def forName(n):
        return TypeInfo.byname[n]

    @staticmethod
    def auto_castable(current, desired):
        current_rank = TypeInfo.forType(current).rank
        desired_rank = TypeInfo.forType(desired).rank
        return current_rank <= desired_rank

# static members
BOOL = TypeInfo('bool', bool, np.bool_, 1)
INT = TypeInfo('int', int, np.int_, 2)
REAL = TypeInfo('real', float, np.float_, 3)
TIME = TypeInfo('time', float, np.float_, 4)

# Real types
TYPES = (BOOL, INT, REAL, TIME)

# This pseudo-type is used to manipulate internal data. There are no
# variables of this type, only intermediate results.
OBJ = TypeInfo('object', object, lambda x: np.array(x, dtype=object),5)
ALL_TYPES = TYPES+(OBJ,)

# Maps used to translate between type systems
TypeInfo.byname = {t.name : t for t in TYPES}
TypeInfo.bytype = {t.dtype : t  for t in TYPES}




#
# Shape management routines
#


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
    

#
# Operator models description
#

# An operator model is a collection of routines and information
# related to types of operators in the expressions of Vectorl
#
# An operator model must provide:
#
# - The operator arity, or None for variable-arity operators
#
# - result_type(): a function computing the result type, from the 
#   input operands. 
#   If it returns None, then there was a type-related error (e.g., 
#   wrong imput types).
#
# - result_size(): A function computing the shape of the result, 
#   given the operands.
#   If it returns None, or raises, there was an error regarding sizes.
#
# - result_const(): A function computing constness based on the 
#   operands.
#
# - result_lvalue(): A function computing lvaluedness based on the
#   operands.
#

# utilities related to result type

def std_result_type(*args):
    '''
    Return the result type applying standard C++ conversions.
    '''
    return np.result_type(*[a.type for a in args])

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
        s = std_result_type(*[a.type for a in args])
        s = s.char * len(args)

        tt = ''.join(s) + "->"

        for m in uf.types:
            if m.startswith(tt):
                rt=m[:len(tt)]
                return np.dtype(rt)
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
    # name,   operator,     impl,       arity,  result_type,    result_size,    result_const
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
        self.operator = operator    # from the ast (e.g., '-', '!', etc)
        self.impl = impl            # the executable function 

        self.arity = arity          # number of arguments (None: unbounded)
        self.result_type = result_type
        self.result_size = result_size
        self.result_const = result_const

    result_lvalue = lambda *args, **kwargs: False

OPERATOR = {}
OPERATOR['unary'] = { op[0] : OperatorModel(* op ) for op in OP1_TABLE }
OPERATOR['binary'] = { op[0] : OperatorModel(* op ) for op in OP2_TABLE }


# Five special operators: concat cast funcall cond index

class CastOperatorModel:
    def __init__(self, ctype):
        self.operator = ctype.name
        self.ctype = ctype
        self.arity = 1

    def impl(self, arg):
        return self.ctype

    def result_type(self, arg):
        return self.ctype

    def result_size(self, arg):
        return arg.shape

    def result_const(self, arg):
        return arg.const

    result_lvalue = lambda *args, **kwargs: False

OPERATOR['cast'] = { t.name: CastOperatorModel(t.dtype) for t in TYPES }


class ConcatOperatorModel:
    def __init__(self):
        self.operator = 'concat'
        self.arity = None

    @staticmethod
    def concat(*args):
        ndim = {a.ndim for a in args}
        if len(ndim)!=1:
            raise ValueError("all arguments must have the same dimension")
        ndim = ndim.pop()
        if ndim:
            return np.concatenate(args)
        else:
            return np.array(args)

    def impl(self, *args):
        return self.concat

    @staticmethod
    def result_size(*args):
        sizes = [a.shape for a in args]
        ndim = len(sizes[0])
        if any(len(s)!=ndim for s in sizes):
            return None
        if ndim==0:
            return (len(sizes),)
        else:
            tsizes = {s[1:] for s in sizes}
            bsize = compute_broadcast_shape(tsizes)
            if bsize is None:
                return None
            ssize = sum(s[0] for s in sizes)
            return (ssize,)+bsize

    result_type = staticmethod(std_result_type)

    result_const = staticmethod(all_const)

    result_lvalue = staticmethod(lambda *args, **kwargs: False)

OPERATOR['concat'] = ConcatOperatorModel()


# cond
class CondOperatorModel:
    def __init__(self):
        self.operator = 'cond'
        self.arity = 3

    def impl(self, *args):
        return np.where

    def result_type(self, *args):   
        return std_result_type(args[1], args[2])

    result_size = broadcast_shape

    result_const = all_const

    result_lvalue = lambda *args, **kwargs: False



OPERATOR['cond'] = CondOperatorModel()

# funcall

# function calls do not refer to Vectorl functions but to
# 'builtin' functions (library, aggregate etc).

# TBD

# index expressions are like  A[idx]. We treat 'idx' as a separate kind of expression
# called a 'strider'.

class IndexOperatorModel:
    def __init__(self):
        self.operator = 'index'
        self.arity = 2

    def impl(self, A, s):
        def indexop(A, s):
            # we need to transform s first!
            # numpy does all the magic!
            return A[s]

    @staticmethod
    def result_type(A, s):
        return A.type

    @staticmethod
    def normalize_strider(a, s):
        # remove the ellipsis
        if ... in s:
            pos = s.index(...)
            s1 = s[:pos]
            s2 = s[pos+1:]
            n = len(a)+s1.count('_') +s2.count('_') -len(s1)-len(s2)
            if n<0:
                raise ValueError("Too many dimensions in index")
            s = s1+('_',)*n + s2

        # add dimensions at the end, if needed
        m = len(s)-s.count('_')
        if m < len(a):
            s = s + (slice(None,None,None),)*(len(a)-m)
        return s

    @staticmethod
    def result_size(A, strider):
        s = strider.indexer
        a = A.shape

        # normalize
        s = normalize_strider(a, s)

        # ok, now compute the final size
        result = []
        i=0
        for iop in s:
            if iop == '_':
                result.append(1)
                continue
            elif isinstance(iop, slice):
                if iop.start is None and iop.stop is None:
                    result.append(a[i])
                elif iop.stop is None:
                    result.append(1)
                else:
                    if not (0 <= iop.stop <= a[i]):
                        raise IndexError("specified slice size is too large")
                    result.append(iop.stop)
                i += 1
            else:
                i+=1

        return tuple(result)

    result_const = all_const

    def result_lvalue(self, A, strider):
        return A.lvalue


OPERATOR['index'] =IndexOperatorModel()


#
# Expression tree. This is used for inference.
#


@model
class ExprNode:
    '''Base class for expression tree nodes.'''

    # All are nullable. None means 'unknown'
    type = attr(TypeInfo)
    shape = attr(tuple)
    lvalue = attr(bool)
    const = attr(bool)

    def is_scalar(self):
        assert self.shape is not None
        return self.shape in (tuple(), (1,))

    def auto_castable(self, totype):
        assert self.type is not None
        return self.type.auto_castable(totype)

    def cast(self, T):
        '''Return a new expression casting this one to TypeInfo T'''
        opmodel = OPERATOR['cast'][T.name]
        return create_operator_node(opmodel, expr)

    def cast_if_needed(self, T):
        if self.type != totype:
            return self.cast(T)
        else:
            return self

    def broadcastable(self, other):
        '''Return true if other is broadcastable to self.'''
        return broadcastable(self.shape, other.shape)

@model
class VarRef(ExprNode):
    '''
    Leaf node fore expression trees. Reference to a Variable.
    '''
    def __init__(self, var):
        self.var=var
        self.type = var.type
        self.const = False
        self.lvalue = True
        self.shape = self.var.initval.shape

@model
class Constant(ExprNode):
    '''
    Leaf node for expression trees.
    A compile-time constant.
    '''

    def __init__(self, val, type=None):
        self.type = type if type is not None else TypeInfo.forLiteral(val)
        self.value = self.type.dtype.type(val)
        self.shape = self.value.shape
        self.const = True
        self.lvalue = False

@model
class Operator(ExprNode):
    '''
    Internal node for expression trees: an operator.
    '''

    def __init__(self, op, *args):
        self.op = op
        self.args = args

        # infer type
        self.type = TypeInfo.forType(op.result_type(*args))
        if self.type is None:
            raise ValueError("Failed to get result type for %s expression", opmodel.operator)
    
        # infer shape
        self.shape = op.result_size(*args)
        if self.shape is None:
            raise ValueError("Failed to get result shape for %s expression", opmodel.operator)

        # infer constness
        self.const = op.result_const(*args)

        # infer lvaluedness
        self.lvalue = op.result_lvalue(*args)

        self.value = None

        impl = self.op.impl(* self.args)

        if self.const:
            # Compute the value eagerly!
            assert all(isinstance(a, Constant) for a in self.args)
            argvals = [a.value for a in args]
            self.value = impl(*argvals)

    def std_result_dtype(self):
        '''
        Return the result dtype applying standard C++ conversions.
        This is implemented by numpy.
        '''
        return np.result_type(*[a.type.dtype for a in self.args])

    def operator_arity(self):
        raise NotImplemented

    def arity(self):
        return len(self.args)

    def result_type(self):
        raise NotImplemented

    def result_size(self):
        raise NotImplemented

    def result_const(self):
        return all(a.const for a in self.args)

    def result_lvalue(self):
        return False


@model
class UFuncOperator(Operator):
    '''
    UFunc operators are implemented as numpy UFuncs.
    '''

    ufunc = attr(np.ufunc, nullable=False)
    oper = attr(str, nullable=False)

    def __init__(self, oper, ufunc, *args):
        self.ufunc = ufunc
        self.oper = oper
        super().__init__(args)


    def result_dtype(self):
        s = self.std_result_dtype()
        s = s.char * self.arity()

        tt = ''.join(s) + "->"

        for m in uf.types:
            if m.startswith(tt):
                rt=m[:len(tt)]
                return np.dtype(rt)
        raise ValueError("Cannot find legal operator combination")

    def result_type(self):
        return TypeInfo.fromType(self.std_result_dtype())

    def result_size(self):
        return broadcast_shape(* self.args)

    def operator_arity(self):
        return self.ufunc.nin



class CastOperator(Operator):
    '''Type casting operator'''

    dtype = attr(np.dtype)

    def __init__(self, ctype, arg):
        self.ctype = ctype
        self.dtype = ctype.dtype
        super().__init__(arg)

    def impl(self):
        return self.dtype.type

    def result_type(self):
        return self.ctype

    def result_size(self):
        return self.args[0].shape

    def result_const(self):
        return self.args[0].const

    def operator_arity(self):
        return None


class ConcatOperator(Operator):
    '''
    Concatenation operator
    '''
    def __init__(self, *args):
        super().__init__(*args)

    @staticmethod
    def concat(*args):
        ndim = {a.ndim for a in args}
        if len(ndim)!=1:
            raise ValueError("all arguments must have the same dimension")
        ndim = ndim.pop()
        if ndim:
            return np.concatenate(args)
        else:
            return np.array(args)

    def impl(self):
        return self.concat

    def result_size(self):
        sizes = [a.shape for a in self.args]
        ndim = len(sizes[0])
        if any(len(s)!=ndim for s in sizes):
            return None
        if ndim==0:
            return (len(sizes),)
        else:
            tsizes = {s[1:] for s in sizes}
            bsize = compute_broadcast_shape(tsizes)
            if bsize is None:
                return None
            ssize = sum(s[0] for s in sizes)
            return (ssize,)+bsize

    def result_type(self):
        return TypeInfo.fromType(self.std_result_dtype())


# cond
class CondOperator:
    '''The conditional ?: operator'''

    def __init__(self, *args):
        cond, yes, no = args
        super()._init__(*args)
        assert len(args)==3

    def impl(self):
        return np.where

    def result_type(self):   
        return TypeInfo.byType(std_result_type(yes, no))


# funcall

# function calls do not refer to Vectorl functions but to
# 'builtin' functions (library, aggregate etc).

# TBD


# index expressions are like  A[idx]. We treat 'idx' as a separate kind of expression
# called a 'strider'.

class IndexOperator(Operator):
    def __init__(self, arg):
        self.args = (arg,)

    def impl(self, A, s):
        def indexop(A, s):
            # numpy does all the magic!
            return A[s]

    def result_type(self, A, s):
        return A.type

    @staticmethod
    def normalize_strider(a, s):
        # remove the ellipsis
        if ... in s:
            pos = s.index(...)
            s1 = s[:pos]
            s2 = s[pos+1:]
            n = len(a)+s1.count('_') +s2.count('_') -len(s1)-len(s2)
            if n<0:
                raise ValueError("Too many dimensions in index")
            s = s1+('_',)*n + s2

        # add dimensions at the end, if needed
        m = len(s)-s.count('_')
        if m < len(a):
            s = s + (slice(None,None,None),)*(len(a)-m)
        return s

    @staticmethod
    def result_size(A, strider):
        s = strider.indexer
        a = A.shape

        # normalize
        s = normalize_strider(a, s)

        # ok, now compute the final size
        result = []
        i=0
        for iop in s:
            if iop == '_':
                result.append(1)
                continue
            elif isinstance(iop, slice):
                if iop.start is None and iop.stop is None:
                    result.append(a[i])
                elif iop.stop is None:
                    result.append(1)
                else:
                    if not (0 <= iop.stop <= a[i]):
                        raise IndexError("specified slice size is too large")
                    result.append(iop.stop)
                i += 1
            else:
                i+=1

        return tuple(result)

    result_const = all_const

    def result_lvalue(self, A, strider):
        return A.lvalue





















@model
class ExpressionFactory:

    operator_classes = {'unary','binary','cond','cast','index','concat'}
    unary = { '+','-','!','~' }
    binary = {  }

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


#    def get_operator(self, op, *args):


