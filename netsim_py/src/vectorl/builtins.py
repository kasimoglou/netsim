
# Builtin functions.
#
# These functions are different from Vectorl 'func' objects, 
# both semantically and pragmatically.
# They implement basic functionality (library, aggregate etc)
# that is more akin to 'operators'
#


from models.mf import *
from vectorl.expr import *
import numpy as np

builtins = {}

@model
class Builtin(Operator):

	@classmethod
	def bind_func(cls, *args):
		return cls(*args)

	def bind(self, argmap):
		'''
		In builtin nodes, binding requires invoking the
		constructor.
		'''
		return self.bind_func(* self.bind_args(argmap))

	def description(self):
	    return "%s" % self.__class__.__name__


@model
class shapeof(Builtin):
	'''
	Returns the shape of the operand.
	'''
	def __init__(self, arg):
		super().__init__('shapeof', arg)

	def impl(self):
		return lambda x: np.array(x.shape)

	def result_type(self):
		return INT 
	def result_shape(self):
		argshape = self.args[0].shape
		return (len(argshape),) if argshape is not None else None
	def result_const(self):
		return True
	def operator_arity(self):
		return 1

	def const_value(self):
		return np.array(self.args[0].shape) if self.args[0].shape else None


builtins['shapeof'] = shapeof


@model
class __aggregate(Builtin):
	'''
	Returns the aggregate of the operand.
	'''
	func = None
	def __init__(self, name, arg, axis):
		super().__init__(name, arg, axis)

	def impl(self):
		return lambda x, ax: self.func.reduce(x, ax, 
			dtype=self.args[0].type.dtype)

	def result_type(self):
		if not self.args_proper_type(): return None
		if self.args[1].type != INT:
			fail("Aggregate axis is not an integer")
		return self.args[0].type

	def result_shape(self):
		if not self.args_proper_shape(): return None
		if not self.args[1].is_proper(): return None
		if self.args[1].type != INT:
			fail("Aggregate axis is not an integer")
		if not self.args[1].is_scalar():
			fail("Aggregate axis is not scalar")
		if not self.args[1].const:
			fail("Aggregate axis is not constant")

		argshape = tuple(self.args[0].shape)
		axis = self.args[1].value

		if len(argshape)<=axis or axis<-len(argshape):
			fail("Aggregate axis %d out of range, for shape %s",axis,argshape)
		
		if axis<0: axis += len(argshape)

		return argshape[:axis]+argshape[axis+1:]


	def result_const(self):
		return self.args[0].result_const()

	def operator_arity(self):
		return 2


@model
class sum(__aggregate):
	func = np.add
	def __init__(self, arg, axis):
		super().__init__('sum',arg,axis)

builtins['sum'] = sum

@model
class product(__aggregate):
	func = np.add
	def __init__(self, arg, axis):
		super().__init__('product',arg,axis)

builtins['product'] = product

@model
class maximum(__aggregate):
	func = np.maximum
	def __init__(self, arg, axis):
		super().__init__('maximum',arg,axis)

builtins['maximum'] = maximum

@model
class minimum(__aggregate):
	func = np.minimum
	def __init__(self, arg, axis):
		super().__init__('minimum',arg,axis)

builtins['minimum'] = minimum



# Functions

def def_unary_ufunc(name, ufunc):
	class Func(UFuncOperator, Builtin):
		def __init__(self, arg):
			super().__init__(name, ufunc, arg)
	return Func


@model 
class UnaryUFunc(Builtin):
    ufunc = attr(np.ufunc, nullable=False)

    def __init__(self, oper, ufunc, arg):
        self.ufunc = ufunc
        super().__init__(oper, arg)


    def result_dtype(self):
        s = self.std_result_dtype()
        s = s.char * self.arity

        tt = ''.join(s) + "->"

        for m in self.ufunc.types:
            if m.startswith(tt): 
                rt=m[len(tt):]
                return np.dtype(rt)
        fail("error: illegal operand types: %s",tt)

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


class Exp(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('exp', np.exp, arg)
builtins['exp'] = Exp

class Log(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('log', np.log, arg)
builtins['log'] = Log

class Log2(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('log2', np.log2, arg)
builtins['log2'] = Log2

class Log10(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('log10', np.log10, arg)
builtins['log10'] = Log10

class Sqrt(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('sqrt', np.sqrt, arg)
builtins['sqrt'] = Sqrt


class Sin(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('sin', np.sin, arg)
builtins['sin'] = Sin

class Cos(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('cos', np.cos, arg)
builtins['cos'] = Cos

class Tan(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('tan', np.tan, arg)
builtins['tan'] = Tan

class ArcSin(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('arcsin', np.arcsin, arg)
builtins['arcsin'] = ArcSin

class ArcCos(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('arccos', np.arccos, arg)
builtins['arccos'] = ArcCos

class ArcTan(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('arctan', np.arctan, arg)
builtins['arctan'] = ArcTan

class IsNan(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('isnan', np.arctan, arg)
builtins['isnan'] = IsNan

class IsInf(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('isinf', np.arctan, arg)
builtins['isinf'] = IsInf

class Floor(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('floor', np.arctan, arg)
builtins['floor'] = Floor

class Ceil(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('ceil', np.arctan, arg)
builtins['ceil'] = Ceil

class Trunc(UnaryUFunc):
	def __init__(self, arg):
		super().__init__('trunc', np.arctan, arg)
builtins['trunc'] = Trunc




##################################
# Array constructors
##################################



class Range(Builtin):
	def __init__(self, arg):
		super().__init__('range', arg)

	def impl(self):
		return lambda x: np.arange(x)

	def result_type(self):
		return INT 

	def result_shape(self):
		a = self.args[0]
		if not a.is_proper(): return None
		if not a.const:
			fail("range with non-constant operand")
		if a.type!=INT:
			fail("range with non-integer operand: %s",a.type)
		if not a.is_scalar():
			fail("range with non-scalar operand")
		return (a.value,)

	def result_const(self):
		return True

	def operator_arity(self):
		return 1

builtins['range'] = Range


class Fill(Builtin):
	def __init__(self, shp, val):
		super().__init__('fill', shp, val)

	def impl(self):
		return lambda s,v: np.full(s,v, dtype=self.args[1].type.dtype)

	def result_type(self):
		return self.args[1].type

	def result_shape(self):
		s = self.args[0]
		if not s.is_proper(): return None
		if not s.const:
			fail("shape operand is not constant`")
		if s.type!=INT:
			fail("range with non-integer shape: %s",s.type)
		if not s.is_scalar() and not len(s.shape)==1:
			fail("range with illegal shape")
		if s.is_scalar():
			return (s.value,)
		else:
			return tuple(s.value) 

	def result_const(self):
		return self.args[1].const

	def operator_arity(self):
		return 2

builtins['fill'] = Fill

#################################################################
#  The sys module builtins, do not go into the 'builtins' map
#################################################################


@model
class SysBuiltin(Builtin):
	'''
	Marker superclass to indicate that a builtin needs access to
	the stack machine's api.
	'''
	pass

sys_builtins = {}


@model
class sys_now(SysBuiltin):
	'''
	Returns the current simulation time.
	'''
	def __init__(self):
		super().__init__('now')

	def impl(self):
		return lambda sm: sm.now

	def result_type(self):
		return TIME

	def result_shape(self):
		return tuple()

	def result_const(self):
		return False

	def operator_arity(self):
		return 0

sys_builtins['now'] = sys_now

