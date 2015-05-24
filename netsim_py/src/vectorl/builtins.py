
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


#################################################################
#  The sys module builtins, do not go into the 'builtins' map
#################################################################


@model
class SysBuiltin(Builtin):
	'''
	Marker superclass to indicate that a builtin needs access to
	the stack amchine's api.
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

