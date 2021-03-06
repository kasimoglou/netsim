#
# This is part of the VectorL python runtime engine.
# This is the part where computations are described.
# It is based on numpy.
#

from collections import namedtuple
import numpy as np
from models.mf import *
from models.validation import fail, warn, inform, snafu
from simgen.utils import docstring_template

from vectorl.base import SourceItem
from vectorl.typeinfo import *

#
# Shape management routines
#

def compute_broadcast_shape(shapes):
    '''
    Compute a broadcast size where all shapes in 'shapes'
    (a sequence) can be broadcast. Return None if it is not
    possible.
    '''

    def prepad(tup, l):
        '''
        Prepad a tuple tup to length l, with 1's
        '''
        return (1,)*(l-len(tup))+tup


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

def broadcastable(lhs, rhs):
    '''return true if the rhs shape is broadcastable to
    the lhs.
    '''
    if len(lhs)<len(rhs):
        return False
    return all(x==y or y==1 for x,y in zip(lhs, rhs))

def broadcast_shape(*args):
    if len(args)==0: return tuple()
    if len(args)==1: return args[0].shape
    return compute_broadcast_shape(a.shape for a in args)



########################################################
#
# Expression tree. This is used for inference.
#
########################################################

@model
class ExprNode(SourceItem):
    '''
    Base class for expression tree nodes.

    The basic properties of an expression tree node are:
    - its type
    - its shape 
    - its lvalue-dness
    - its (compile-time) constness

    Any of these 4 properties may be unknown (None) at some point, in
    which case, the node is 'improper', else it is proper.
    '''

    # All are nullable. None means 'unknown'
    type = attr(TypeInfo, nullable=True, default=None)
    shape = attr(tuple, nullable=True, default=None)
    lvalue = attr(bool, nullable=True, default=None)
    const = attr(bool, nullable=True, default=None)

    def is_scalar(self):
        '''
        Returns true if the shape is empty.
        '''
        assert self.shape is not None
        return len(self.shape)==0

    def auto_castable(self, totype):
        '''
        Determines whether the type of the node is automatically
        castable to the given type.
        '''
        assert self.type is not None
        return self.type.auto_castable(totype)

    def cast_if_needed(self, T):
        '''
        If needed, return a cast operator with this node as 
        argument.
        '''
        if self.type is not T:
            return self.cast(T)
        else:
            return self

    def broadcastable(self, other):
        '''Return true if other is broadcastable to self.'''
        return broadcastable(self.shape, other.shape)

    def is_proper(self):
        '''
        Return True if the node is fully initialized.
        '''
        return None not in (self.type, self.shape, 
            self.lvalue, self.const)

    def bind(self, argmap):
        '''
        Bind (recursively down the tree) any unbound argument in the node's subtree
        to the given arguments and then return a clone with the new binding.

        This way Function objects are implemented.
        '''
        raise NotImplementedError()


    #
    # Define operators
    #

    # binary
    def __add__(self, other): return UFuncOperator('+', np.add, self, other)
    def __sub__(self, other): return UFuncOperator('-', np.subtract, self, other)
    def __mul__(self, other): return UFuncOperator('*', np.multiply, self, other)
    def __truediv__(self, other): return UFuncOperator('/', np.divide, self, other)
    def __mod__(self, other): return UFuncOperator('%', np.remainder, self, other)
    def __lshift__(self, other): return UFuncOperator('<<', np.left_shift, self, other)
    def __rshift__(self, other): return UFuncOperator('>>', np.right_shift, self, other)
    def __and__(self, other): return UFuncOperator('&', np.bitwise_and, self, other)
    def __xor__(self, other): return UFuncOperator('^', np.bitwise_xor, self, other)
    def __or__(self, other): return UFuncOperator('|', np.bitwise_or, self, other)

    # unary
    def __neg__(self): return UFuncOperator('-', np.negative, self)
    def __invert__(self): return UFuncOperator('~', np.invert, self)
    def __pos__(self): return self

    # relational
    def __lt__(self, other): return UFuncOperator('<', np.less, self, other)
    def __le__(self, other): return UFuncOperator('<=', np.less_equal, self, other)
    def __gt__(self, other): return UFuncOperator('>', np.greater, self, other)
    def __ge__(self, other): return UFuncOperator('>=', np.greater_equal, self, other)

    def __eq__(self, other):
        if isinstance(other, ExprNode):
            return UFuncOperator('==', np.equal, self, other)
        else:
            return False
    def __ne__(self, other): 
        if isinstance(other, ExprNode):
            return UFuncOperator('!=', np.not_equal, self, other)
        else:
            return False

    # cast
    def cast(self, T):
        '''Return a new expression casting this one to TypeInfo T'''
        return CastOperator(T,self)

    def __getitem__(self, idx):
        return IndexOperator(self, Indexer(idx, self.shape))


def LNOT(expr):  return UFuncOperator('!', np.logical_not, expr)
def LAND(e1, e2): return UFuncOperator('&&', np.logical_and, e1, e2)
def LOR(e1, e2): return UFuncOperator('||', np.logical_or, e1, e2)


#################################################
#
# Leaf nodes 
#
#################################################

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

    def bind(self, argmap): return self

    def description(self):
        return self.var.name

@model
class Literal(ExprNode):
    '''
    Leaf node for expression trees.
    A compile-time literal.
    '''

    def __init__(self, val, type=None):
        self.type = type if type is not None else TypeInfo.forLiteral(val)
        self.value = self.type.dtype.type(val)
        #print("VALUE=",self.value,"of type",self.value.__class__," for type=",self.type,"where val type is",val.__class__)
        self.shape = self.value.shape
        self.const = True
        self.lvalue = False

    def bind(self, argmap): return self

    def description(self):
        return str(self.value)


@model
class Parameter(ExprNode):
    '''
    Leaf node for unspecified parameters. Parameters may
    not have any information available (including type), except
    lvalued-ness. Parameters are not lvalues.
    '''
    name = attr(str, nullable=False)

    def __init__(self, name, type=None, shape=None, const=None):
        self.name = name
        self.type = type
        self.shape = shape
        self.const = const
        self.lvalue = False

    def bind(self, argmap):
        return argmap.get(self.name, self)

    def description(self):
        return "parameter '%s'" % self.name

@model
class Operator(ExprNode):
    '''
    Internal node for expression trees: an operator.

    An operator's model (class) is a collection of routines 
    related to the properties of this expression node.

    An operator model must provide:

    - operator_arity(), an integer, or None for variable-arity operators.

    - result_type(): a function computing the result type, from the 
    input operands. 

    - result_shape(): A function computing the shape of the result, 
    given the operands.

    - result_const(): A function computing constness based on the 
    operands.  Returns boolean.

    - result_lvalue(): A function computing lvaluedness based on the
    operands. Returns boolean.

    If any of these functions returns None, the result cannot be determined
    yet because arguments are not proper yet.
    If it raises an exception, then there was an error (e.g., wrong number 
    or type of arguments, bad operand type, etc.). 
    '''

    op = attr(str, nullable=False)
    args = attr(tuple, nullable=False)

    def __init__(self, op, *args):
        super().__init__()
        self.op = op
        assert all(isinstance(a, ExprNode) for a in args)
        self.args = args
        self.initialize()

    def initialize(self):
        # infer type
        if self.type is None:
            self.type = self.result_type()
    
        # infer shape
        if self.shape is None:
            self.shape = self.result_shape()

        # infer constness
        if self.const is None:
            self.const = self.result_const()

        # infer lvaluedness
        if self.lvalue is None:
            self.lvalue = self.result_lvalue()

        self.value = self.const_value()

    def const_value(self):
        '''
        The value of this node as a compile-time constant. If the
        node is not const or proper, returns None.
        '''
        if self.is_proper() and self.const:
            argvals = [a.value for a in self.args]
            return self.impl()(* argvals)
        return None


    def bind_args(self, argmap):
        '''
        Helper method to recursively propagate a bind call to the arguments
        and return a tuple with bound arguments.
        '''
        return tuple(arg.bind(argmap) for arg in self.args)


    def std_result_dtype(self):
        '''
        Return the result dtype applying standard C++ conversions to the
        arguments. This is implemented by numpy.
        '''
        return np.result_type(* tuple(a.type.dtype for a in self.args))

    def operator_arity(self):
        raise NotImplementedError()

    @property
    def arity(self):
        return len(self.args)

    def result_type(self):
        raise NotImplementedError()

    def result_shape(self):
        raise NotImplementedError()

    def result_const(self):
        return all(a.const for a in self.args) if self.args_proper_const() else None

    def result_lvalue(self):
        return False

    def impl(self):
        '''
        Return the implementation of this operator the
        arguments: a function that can be called on 
        values consistent with the arguments in terms
        of shape and type.
        '''
        raise NotImplementedError()

    # Helper methods
    def args_proper(self, attrname=None):
        if attrname is None:
            return all(a.is_proper() for a in self.args)
        return all(getattr(a,attrname,None) is not None for a in self.args)
    def args_proper_type(self): return self.args_proper('type')
    def args_proper_shape(self): return self.args_proper('shape')
    def args_proper_lvalue(self): return self.args_proper('lvalue')
    def args_proper_const(self): return self.args_proper('const')

    def description(self):
        return "operator %s/%d" % (self.op, self.arity)


@model
class UFuncOperator(Operator):
    '''
    UFunc operators are implemented as numpy UFuncs.
    '''

    ufunc = attr(np.ufunc, nullable=False)

    def __init__(self, oper, ufunc, *args):
        self.ufunc = ufunc
        super().__init__(oper, *args)


    def result_dtype(self):
        s = self.std_result_dtype()
        s = s.char * self.arity

        tt = ''.join(s) + "->"

        for m in self.ufunc.types:
            if m.startswith(tt): 
                rt=m[len(tt):]
                return np.dtype(rt)
        fail("error: illegal operand types")

    def result_type(self):
        return TypeInfo.forType(self.result_dtype()) \
            if self.args_proper_type() else None

    def result_shape(self):
        return broadcast_shape(* self.args) \
            if self.args_proper_shape() else None

    def operator_arity(self):
        return self.ufunc.nin

    def impl(self):
        return self.ufunc

    def bind(self, argmap):
        if self.is_proper(): return self
        return UFuncOperator(self.op, self.ufunc, * self.bind_args(argmap))


@model
class CastOperator(Operator):
    '''Type casting operator'''

    ctype = attr(TypeInfo)
    dtype = attr(np.dtype)

    def __init__(self, ctype, arg):
        self.ctype = ctype
        self.dtype = ctype.dtype
        super().__init__('cast', arg)

    def impl(self):
        return self.dtype.type

    def result_type(self):
        return self.ctype

    def result_shape(self):
        return self.args[0].shape

    def result_const(self):
        return self.args[0].const

    def operator_arity(self):
        return 1

    def bind(self, argmap):
        if self.is_proper(): return self
        return CastOperator(self.ctype, * self.bind_args(argmap))

    def description(self):
        return "cast(%s)" % self.ctype.name

@model
class ArrayOperator(Operator):
    '''
    Array creation operator
    '''
    def __init__(self, *args):
        super().__init__('array', *args)

    @staticmethod
    def array(*args):
        return np.array(np.broadcast_arrays(*args))

    def impl(self):
        return self.array

    def result_shape(self):
        if self.args_proper_shape():
            argshape = broadcast_shape(*self.args)
            return (len(self.args),)+argshape
        return None

    def result_type(self):
        return TypeInfo.forType(self.std_result_dtype()) \
            if self.args_proper_type() else None

    def operator_arity(self):
        return None

    def bind(self, argmap):
        if self.is_proper(): return self
        return ArrayOperator(* self.bind_args(argmap))


# shorthand
Array = ArrayOperator


@model
class ConcatOperator(Operator):
    '''
    Array concatenation operator
    '''
    all_similar = attr(bool, default=False)

    def __init__(self, *args):
        assert len(args)>1
        super().__init__('concat', *args)

    @staticmethod
    def concat(*args):
        return np.concatenate(args)

    def impl(self):
        return self.concat

    def result_shape(self):
        # argument shapes must broadcast on all coordinates except the
        # first.
        if not self.args_proper_shape(): return None
        shapes = set()
        D = 0
        for arg in self.args:
            shape = arg.shape
            if shape is None:
                return None
            if shape == tuple():
                fail("concatenation of scalars is not supported")
            D += shape[0]
            shapes.add(shape[1:])
        if len(shapes)==1:
            # all operands have same residual shape!
            self.all_similar = True
            return (D,)+shapes.pop()
        return (D,)+compute_broadcast_shape(shapes)


    def result_type(self):
        if not self.args_proper_type(): return None
        return TypeInfo.forType(self.std_result_dtype())

    def result_lvalue(self):
        '''
        A concatenation is an l-value iff
        '''
        if not self.shape or not self.args_proper_lvalue(): return None
        return self.all_similar and all(arg.lvalue for arg in self.args)

    def operator_arity(self):
        return None


    def bind(self, argmap):
        if self.is_proper(): return self
        return ConcatOperator(* self.bind_args(argmap))


# convenience name
Concat = ConcatOperator



# cond
@model
class CondOperator(Operator):
    '''The conditional ?: operator'''

    def __init__(self, cond, yes, no):
        super().__init__('cond', cond, yes, no)

    def impl(self):
        return np.where

    def result_type(self):
        cond, yes, no = self.args

        if None not in (yes.type, no.type):
            return TypeInfo.forType(self.std_result_dtype())

    def result_shape(self):
        if self.args_proper_shape():
            return broadcast_shape(* self.args)


    def result_const(self):
        '''Here, we check the case where cond is uniformly
        constant (all values are boolean equivalent) and
        the corresponding operand is const
        '''
        cond, yes, no = self.args
        if not self.args_proper(): return None
        if cond.const:
            if yes.const and no.const: return True
            if np.all(cond.value) and yes.const: return True
            if np.all(np.logical_not(cond.value)) and no.const: return True
            return False
        else:
            return yes.const and no.const and\
                np.all(np.equal(yes.value, no.value))

    def operator_arity(self):
        return 3

    def bind(self, argmap):
        if self.is_proper(): return self
        return CondOperator(* self.bind_args(argmap))

#shorthand
IF = CondOperator


# index expressions are like  A[idx]. We treat 'idx' as a separate kind of expression
# called a 'indexer'.

@model
class Indexer(Operator):
    '''
    An auxiliary type of expression node, containing the slice analysis
    logic for the IndexOperator
    '''

    index = attr(tuple)       # the original index tuple
    array_shape = attr(tuple, default=None) # the shape of the indexed array

    # used to create implementation function
    impl_arg = attr(list)   # the non-const arguments from all_args
    impl_expr = attr(list)  # list of strings to create impl
    result_shape = attr(list)  # a list used to construct the new shape

    def __init__(self, index, array_shape=None):
        '''
        Pass in an index tuple
        '''

        self.index = index
        all_args = self.collect_args()
        super().__init__('indexer', *all_args)

        self.type = OBJ
        self.shape = None
        self.const = None
        self.lvalue = False

        self.process_index(array_shape)
        if self.array_shape is not None:
            self.initialize()


    # Operator definitions
    def result_type(self): return OBJ
    def result_const(self):
        if self.array_shape is None:
            return None
        else:
            return len(self.impl_arg)==0

    def result_shape(self):
        if self.array_shape is None:
            return None
        else:
            return tuple(self.result_shape)
    def operator_arity(self): return None

    def is_proper(self):
        return super().is_proper() and self.array_shape is not None

    def bind(self, argmap, shape):
        if self.is_proper(): return self
        def bind_idx(idx):
            if isinstance(idx, ExprNode):
                return idx.bind(argmap)
            elif isinstance(idx, slice):
                return slice(bind_idx(idx.start), bind_idx(idx.stop),bind_idx(idx.step))
            else:
                return idx

        return Indexer(tuple(bind_idx(i) for i in self.index), shape)

    #
    # getvar and __impl_code are collaborators
    #
    def get_arg_index(self, arg):
        '''
        Get the index of arg in self.args. 
        Note: we cannot use self.args.index(arg), because of
        the overloading of == for ExprNode
        '''
        for i,S in enumerate(self.args):
            if S is arg: return i
        raise ValueError("In get_arg_index: argument not in the list")

    def getvar(self, arg):
        ano = self.get_arg_index(arg)
        var = "args[%d]" % ano
        self.impl_arg.append(arg)
        return var

    @docstring_template
    def __impl_code(self):
        """\
def IDX(*args):
    return tuple([ {{! ','.join(self.impl_expr) }} ])
"""
        return locals()

    def impl(self):
        exec(self.__impl_code(), locals(), globals())
        return IDX

    #
    # Return all the args of this indexer
    #
    def collect_args(self):
        all_args = []
        def collect_expr(e): 
            if isinstance(e, ExprNode): all_args.append(e)
        for S in self.index:
            if isinstance(S, slice):
                collect_expr(S.start)
                collect_expr(S.stop)
                collect_expr(S.step)
            else:
                collect_expr(S)
        return all_args

    def process_index(self, shape):
        if shape is None or not self.args_proper_shape(): return

        idx = list(self.index)
        idx = self.normalize_index(shape, idx)
        self.process_indices(shape, idx)

        self.array_shape = shape
        self.shape = tuple(self.result_shape)

    def normalize_index(self,shape, idx):
        '''
        Remove '...' and replace with sequence of ':'
        '''
        # (a) normalize: remove any ...
        n = idx.count(...)   # number of ellipses
        d = idx.count(None)  # number of new dims
        if n>1:
            fail("error: index contains more than one ellipse (...)")

        if n==1:
            # replace ellipse
            p = idx.index(...)
        else:
            # expand at the end if needed
            assert n==0
            p = len(idx)

        before = idx[0:p]
        after = idx[p+1:]

        l = len(shape)+d-len(before)-len(after)
        if l<0:
            fail("error: too many coordinates in index")
        idx = before+[slice(None,None,None)]*l+after

        assert len(idx)==len(shape)+d
        return idx

    def process_indices(self, shape, idx):
        #
        # Compute new shape and implementation
        # string. The impl. string looks like
        #  lambda a0,a1,...,ak: (3,4,slice(a0,a1,-1), slice(0,20), ...)
        #

        # (a) Compute shapes
        pos = 0
        self.impl_arg = []
        self.impl_expr = []
        self.result_shape = []    # the new shape

        for S in idx:
            if S is None: 
                # new dimension
                self.result_shape.append(1)
                self.impl_expr.append('None')
            elif isinstance(S, ExprNode):
                # normal index
                self.process_normal(S, shape[pos])
                pos += 1
            elif isinstance(S, slice):
                self.process_slice(S, shape[pos])
                pos += 1
            else:
                assert False

        assert pos == len(shape)
        assert len(self.impl_expr) == len(idx)


    def process_slice(self, S, N):
        if S.start is not None: self.check_scalar_int(S.start)
        if S.stop is not None: self.check_scalar_int(S.stop)
        if S.step is not None: self.check_scalar_int_const(S.step)

        # get the step
        step = S.step.value if S.step is not None else 1
        if step==0: fail("error: index step cannot be 0")

        # preprocess start/stop
        start = S.start if S.start is not None else Literal(int(0 if step>0 else -1))
        stop = S.stop if S.stop is not None else Literal(int(N if step>0 else -N-1))

        # compute the size from these arguments

        # case (1): when constness differs, signal an error
        if start.const != stop.const:
            fail("error: cannot determine slice size")

        # case (2): when start and stop are both constant: use python's
        # builtin slice facility to determine size
        if start.const and stop.const:
            size = len(range(* slice(start.value, stop.value, step).indices(N) ))
            if size==0: fail("error: index selects 0 elements")
            if size > N: fail("error: index out of range")
            if start.value < -N-1 or start.value>N: fail("error: index out of range")
            if stop.value < -N-1 or stop.value>N: fail("error: index out of range")

            self.result_shape.append(size)
            self.impl_expr.append("slice(%d,%d,%d)" % (start.value, stop.value, step))
            return

        # case(3): This is a complicated case. First, we try to determine whether
        # the difference of start and stop (i.e.,  stop-start), is constant.
        # See the Diff routine for the limited code analysis checks it performs.
        #
        # Then, we have to take into account negative indices (e.g. A[2:-2] same as
        # the python slice syntax. 
        # Let N be the dimension's size (parameter s above)
        # 
        # Then, p and p-N  (for 0<=p<N) refer to the same 'location' in the dimension
        # (note: the 'past the end' location is just N and the 'before the start' is -N-1)
        #
        # Assume slice  x:y:step with step>0 corresponding to real locations p,q, 
        # with total size S=q-p, where 1<=S<=N.
        # 
        # The algorithm takes D=y-x. There are 4 possibilities
        #  [1] x=p   y=q               then  1<= D <=N     and S = D
        #  [2] x=p-N y=q               then  N+1 <= D <=2N and S = D-N
        #  [3] x=p   y=q-N             then  1-N <= D <=0  and S = D+N
        #  [4] x=p-N y=q-N             then  1<= D <=N     and S = D
        #
        # Therefore, the algorithm checks to see which range D fall in (to assume a
        # non-empty slice) and adjusts accordingly to compute S. Errors are handled by
        # checking the result at runtime.
        #
        # The case where step<0 is handled similarly, with D = x-y. The cases are 
        # the same. 
        D = Diff(S.start, S.stop) if step>0 else Diff(S.stop, S.start)
        if D is None:
            fail("cannot infer a size for array slice")

        if -N<D<=0:
            wsize = D+N
        elif N<D<=2*N:
            wsize = D-N
        elif 1<= D <=N:
            wsize = D
        else:
            fail("slice is out of range")
        # wsize is just the difference between start and stop
        # but the actual shape is ceil(wsize/abs(step))
        self.result_shape.append((wsize+abs(step)-1)//abs(step))

        expr = "slice(%s,%s,%d)" % (self.getvar(S.start), self.getvar(S.stop), step)
        self.impl_expr.append(expr)


    def process_normal(self, S, s):
        self.check_scalar_int(S)
        if S.const:
            pos = S.value
            if pos>s or pos<-s-1:
                fail("Index out of range")
            self.impl_expr.append("%d" % pos)
        else:
            v = self.getvar(S)
            self.impl_expr.append(v)

    def check_scalar_int(self, s):
        if s.type is not INT or not s.is_scalar():
            fail("error: index is not a (scalar) integer")
    def check_scalar_int_const(self, s):
        if s.type is not INT or not s.is_scalar() or not s.const:
            fail("error: index is not a constant integer")





@model
class IndexOperator(Operator):

    def __init__(self, array, indexer):
        assert isinstance(indexer, Indexer)
        assert isinstance(array, ExprNode)
        super().__init__('index', array, indexer)

    @property
    def array(self): return self.args[0]
    @property
    def indexer(self): return self.args[1]

    def impl(self):
        def indexop(A, s):
            # numpy does all the magic!
            ret = A[s]
            if ret.shape != self.shape:
                raise IndexError("Bad index. Expected shape = %s, got %s" 
                    %(ret.shape, self.shape))
            return ret
        return indexop

    def bind(self, argmap):
        A = self.args[0].bind(argmap)
        return IndexOperator(A, self.args[1].bind(argmap, A.shape))

    def result_type(self):
        return self.array.type

    def result_shape(self):
        if self.array.shape is None: return None
        self.indexer.process_index(self.array.shape)
        return self.indexer.shape

    def result_const(self):
        return all(a.const for a in self.args)

    def result_lvalue(self):
        return isinstance(self.array, VarRef)






######################################################
#
# Used to analyze expressions
#
######################################################


def Additive(p):
    '''Return a tuple (a,b) where one of a,b is a constant
    and the other is non-constant, or None. The meaning is 
    "a-b".
    Furthermore, a cannot be None.
    '''

    def add(d, u):
        'd is int, u is tuple'
        assert not isinstance(d, ExprNode)
        assert u[0] is not None
        if isinstance(u[0], ExprNode):
            return (u[0], u[1]-d)
        else:
            return (u[0]+d, u[1])

    def merge(u,v):
        assert u[0] is not None
        assert v[0] is not None
        if u[1] is None:
            return add(u[0], v)
        elif v[1] is None:
            return add(v[0], u)
        # hard case: no None in any
        if isinstance(u[0], ExprNode) and isinstance(v[1], ExprNode) and Equal(u[0], v[1]):
            return (v[0]-u[1], None)
        elif isinstance(u[1], ExprNode) and isinstance(v[0], ExprNode) and Equal(u[0], v[1]):
            return (u[0]-v[1], None)
        else: 
            # Failure!
            return None

    if p is None: return (0, None)
    if p.const: return (p.value, None)
    if isinstance(p, UFuncOperator) and p.operator_arity()==1 and p.op=='-':
        k,l = Additive(p.args[0])
        if l is None: return (-k, None)
        return (l, k)
    if isinstance(p, UFuncOperator) and p.operator_arity()==2 and p.op in ('+','-'):
        a, b = p.args

        u = Additive(a)
        v = Additive(b)
        if p.op=='-':
            if v[1] is None:
                v = (-v[0], None)
            else:
                v = (v[1],v[0])

        m = merge(u,v)
        return (p,0) if m is None else m
    return (p,0)


def Diff(p,q):
    '''
    Return a constant difference between p and q, or None
    if such cannot be proved.
    '''
    def legal(p): return p.is_proper and p.type is INT and p.is_scalar()
    assert legal(p) and legal(q)

    u = Additive(q-p)

    if u[1] is None:
        return u[0]
    else:
        return None

def Equal(a,b):
    '''
    A restricted notion of quality for expression trees: purely structural
    equality. 
    ***This is actually wrong for index operators***
    '''
    if a is b: return True
    if a.const and b.const:
        return np.equal(a,b)
    if a.const or b.const: return False
    if a.__class__ is not b.__class__:
        return False
    if isinstance(a,VarRef) and isinstance(b,VarRef) and a.var is b.var:
        return True
    assert isinstance(a, Operator) and isinstance(b, Operator)
    if a.type is b.type and a.shape==b.shape and a.lvalue==b.lvalue:
        # both are non-const
        if a.op==b.op and a.operator_arity()==b.operator_arity() and a.arity==b.arity:
            if isinstance(a, CastOperator) and a.ctype is not b.ctype:
                return False
            return all(Equal(x,y) for x,y in zip(a.args, b.args))
