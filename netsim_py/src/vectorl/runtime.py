
from vectorl.builtins import SysBuiltin
from vectorl.model import *
from models.validation import snafu

import numpy as np
import heapq
from collections import deque

#
# A simple runner based on a stack machine
#

class StackMachine:
	'''
	This is a mini implementation of a FORTH-like execution engine 
	(a simplified stack machine).
	'''
	def __init__(self):
		self.reset()
		self.varmap = {}		# variable storage
		self.eventmap = {}		# code storage
		self.trace = False

	def reset(self):
		'''
		Reset execution context.
		'''
		self.ostack = []   		# operation stack
		self.dstack = []   		# data stack
		self.event_queue = [] 	# the event queue
		self.event_count = 0  	# event counter
		self.now = TIME(0)    	# the current time
		self.step = 0

	def emit(self, evt, args, after):
		'''
		Emit an event.
		'''
		self.event_count += 1   # used to break ties in the priority queue
		tup = (self.now+after, self.event_count, evt, args)
		heapq.heappush(self.event_queue, tup)

	def trigger(self, evt, args):
		'''
		Trigger processing for event
		'''
		for var, arg in zip(evt.variables, args):
			v = self.varmap[var]
			v[...] = arg
		self.run(self.eventmap[evt])

	def run(self, prog):
		'''
		Load a program on the ostack and iterate until it is empty, or the
		time limit is reached. If time limit is None, no time limit is set.
		'''
		self.ostack.extend(prog.prog)
		while self.ostack:
			op = self.ostack.pop()
			if self.trace:
				self.print_state(op)
			try:
				op(self)
			except Exception as e:
				print("Exception=",e)
				self.print_state(op)
				self.print_stack_labels()
				raise


	def print_state(self, op=None):
		print("step=",self.step,"now=", self.now)
		if op: print("Processing ",op)
		print("Data stack:", self.dstack)
		print("Oper stack:", self.ostack)
		print("Pending:", self.event_queue)
		print()

	def print_stack_labels(self):
		print('Stack trace (top to bottom)')
		for item in reversed(self.ostack):
			if isinstance(item, label):
				print(item)
			else:
				print('\t\t',item)


	def start(self, until=None, steps=None):
		'''
		Process queue events until the specified time,
		or forever when None, or until the number of 'steps'
		is performed, unless None.

		Note that a 'step' is an event dispatch
		'''
		while self.event_queue:
			if until is not None and self.now>until:
				break
			if steps is not None and self.step>=steps:
				break

			item = heapq.heappop(self.event_queue)
			self.step+=1
			if self.trace:
				self.print_state(item)
			self.now, _, evt, args = item
			self.trigger(evt, args)


#
# Stack machine commands
#

class push:
	'''Push a value onto the data stack'''
	__slots__ = ('value')
	def __init__(self, val):
		self.value = val
	def __call__(self, sm):
		sm.dstack.append(self.value)
	def __repr__(self):
		return "<push %s>" % self.value

class pushvar:
	'''Push a variable's value onto the data stack'''
	__slots__ = ('var')
	def __init__(self, var):
		self.var = var
	def __call__(self, sm):
		val = sm.varmap[self.var]
		sm.dstack.append(val.copy())
	def __repr__(self):
		return "<pushvar %s.%s>" % (self.var.model.name, self.var.name)

class pushref:
	'''Push a variable's storage onto the data stack'''
	__slots__ = ('var')
	def __init__(self, var):
		self.var = var
	def __call__(self, sm):
		val = sm.varmap[self.var]
		sm.dstack.append(val)
	def __repr__(self):
		return "<pushref %s.%s>" % (self.var.model.name, self.var.name)


class decl_op:
	def __init__(self, func): self.func = func
	def __call__(self, sm): self.func(sm)
	def __repr__(self): return self.func.__name__

@decl_op
def pop(sm):
	"""
	Pop from the data stack
	"""
	sm.dstack.pop()

@decl_op
def popo(sm):
	"""Pop from the op stack"""
	sm.ostack.pop()

@decl_op
def popo2_if(sm):
	"""Pop and check, if false, pop twice from op stack."""
	cond = sm.dstack.pop()
	if cond: 
		sm.ostack.pop()
		sm.ostack.pop()


class call:
	'''
	Call a function of a given arity with the top of the stack 
	and replace arguments with the result.
	'''
	__slots__ = ('func', 'arity')
	def __init__(self, arity, func):
		self.func = func
		self.arity = arity
	def __call__(self, sm):
		if self.arity:
			args = sm.dstack[-self.arity:]
			del sm.dstack[-self.arity:]
			args.reverse()
		else:
			args = []
		result = self.func(*args)
		if result is not None:
			sm.dstack.append(result)
	def __repr__(self):
		return "<%s/%d>" % (self.func.__name__, self.arity)

class syscall:
	'''
	Call a function of a given arity with the top of the stack 
	and replace arguments with the result.
	'''
	__slots__ = ('func', 'arity')
	def __init__(self, arity, func):
		self.func = func
		self.arity = arity
	def __call__(self, sm):
		if self.arity:
			args = sm.dstack[-self.arity:]
			del sm.dstack[-self.arity:]
			args.append(sm)
			args.reverse()
		else:
			args = [sm]
		result = self.func(*args)
		if result is not None:
			sm.dstack.append(result)
	def __repr__(self):
		return "<%s/%d>" % (self.func.__name__, self.arity)

class Prog:
	'''Add a set of instructions to the operations stack.'''
	__slots__ = ('prog', 'label')
	def __init__(self, prog, label=None):
		self.prog = prog
		self.label = label
	def __repr__(self):
		if self.label:
			return "<%s>" % self.label
		else:
			return "<Prog>"
	def __call__(self, sm):
		sm.ostack.extend(self.prog)

class ExprEval(Prog):
	'''
	Put a stack program on the stack, for computing the value of an expression
	on the given varmap.
	'''
	def __init__(self, expr, label=None):
		super().__init__(list(compile_expression(expr)), label)


class LValueEval(Prog):
	'''
	Put a stack program on the stack, for computing the value of an expression
	on the given varmap.
	'''
	def __init__(self, expr, label=None):
		super().__init__(list(compile_lvalue(expr)), label)


#
#  Compile into stack programs
#

def compile_expression(expr):
	'''
	Yield a stream of opcodes for computing the given expression
	'''
	yield label(repr(expr))
	if isinstance(expr, VarRef):
		yield pushvar(expr.var)
	elif isinstance(expr, Literal):
		yield push(expr.value)
	elif isinstance(expr, Operator):
		if expr.const:
			yield push(expr.value)
		else:
			if isinstance(expr, SysBuiltin):
				yield syscall(expr.arity, expr.impl())
			else:
				yield call(expr.arity, expr.impl())
			for arg in expr.args:
				yield from compile_expression(arg)
	else:
		assert False

def compile_lvalue(expr):
	assert expr.lvalue
	if isinstance(expr, VarRef):
		yield pushref(expr.var)
		yield push((...,))
	elif isinstance(expr, IndexOperator):
		assert isinstance(expr.array, VarRef)
		yield pushref(expr.array.var)
		yield from compile_expression(expr.indexer)
	else:
		assert False


class StmtProg(Prog):
	def __init__(self, stmt, label=None):
		super().__init__(list(compile_statement(stmt)), label)

def assign(var, idx, val):
	assert type(var) is np.ndarray
	if len(idx)==1: idx = idx[0]
	var[idx] = val

def collect(*args):
	return args

class emit:
	__slots__ = ('event')
	def __init__(self, evt):
		self.event = evt
	def __call__(self, sm):
		after, args = sm.dstack[-2:]
		del sm.dstack[-2:]
		sm.emit(self.event, args, after)
	def __repr__(self):
		return "emit(%s.%s)" % (self.event.model.name, self.event.name)

class label:
	__slots__ = ('message')
	def __init__(self, msg):
		self.message = msg
	def __call__(self, sm):
		pass
	def __repr__(self):
		return 'label:'+self.message



def compile_statement(stmt):
	'''
	Yield a stream of opcodes for computing the given statement
	'''
	yield label(repr(stmt))
	if isinstance(stmt, Assignment):
		yield call(3, assign)
		yield LValueEval(stmt.lhs, "E:lhs")
		yield ExprEval(stmt.rhs, "E:rhs")
	elif isinstance(stmt, EmitStatement):
		yield emit(stmt.event)
		yield call(len(stmt.args), collect)
		for arg, param in zip(stmt.args, stmt.event.params):
			yield ExprEval(arg, "E:"+param.name)
		yield ExprEval(stmt.after)
	elif isinstance(stmt, IfStatement):
		yield StmtProg(stmt.then_statement, "P:then")
		yield popo
		yield StmtProg(stmt.else_statement, "P:else")
		yield popo2_if
		yield ExprEval(stmt.condition, "E:if")
	elif isinstance(stmt, PrintStatement):
		yield call(len(stmt.args), print)
		for arg in stmt.args:
			if isinstance(arg, ExprNode):
				yield ExprEval(arg, "E:arg")
			else:
				yield push(arg)
	elif isinstance(stmt, CodeBlock):
		for s in reversed(stmt.statements):
			yield StmtProg(s, "P:"+stmt.origin)
	elif stmt is None or isinstance(stmt,FExpr):
		pass
	else:
		assert False



class Runner(StackMachine):

	def __init__(self, model):
		super().__init__()
		assert isinstance(model, ModelFactory)
		self.model = model
		self.compile_model()

		assert all(type(self.varmap[v]) is np.ndarray for v in model.all_variables())

	def print_tables(self):
		print("Compiled items:",len(self.varmap), "variables,", len(self.eventmap),"events")
		for var, val in self.varmap.items():
			print("Variable","%s.%s" % (var.scope.name,var.name), "=",val)

		for evt in self.eventmap:
			print("Event:", "%s.%s" % (evt.model.name, evt.name))

	def compile_model(self):
		'''
		Compile a model into a stack machine program.
		'''
		# Initialize the variable map
		self.varmap = {}
		for var in self.model.all_variables():
			self.varmap[var] = np.array(var.initval.value)

		# initialize the event programs
		self.eventmap = {}
		for evt in self.model.all_events():
			for var in evt.variables:
				self.varmap[var] = np.array(var.initval.value)
			self.eventmap[evt] = self.compile_event(evt)

	def compile_event(self, evt):
		'''
		Compile the program for an event.
		'''
		all_actions = [label(repr(evt))]
		for action in reversed(evt.actions):
			# compile statement
			all_actions.append(StmtProg(action.statement, "on %s" % evt.name))
		return Prog(all_actions,"actions(%s)" % evt.name)

	def start(self, until=None, steps=None):
		self.emit(self.model.sysmodel['Init'], [], 0)
		super().start(until, steps)

