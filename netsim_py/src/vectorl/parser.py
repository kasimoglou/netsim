
from models.mf import *
from models.constraints import is_legal_identifier
import ply.yacc as yacc
from vectorl.lexer import tokens


@model
class Scope:
	'''An object which defines a new namespace.
	Currently: models, event handlers and functions
	'''
	symtab = attr(dict, nullable=False)
	superscope = ref()
	subscopes = refs(inv=superscope)
	def __init__(self, superscope=None):
		self.symtab = dict()
		self.superscope = superscope

	def lookup(self, name):
		'''Return an object for this name, looking up in this scope
		and its superscope (if any). Return None on failure.
		'''
		if name in self.symtab:
			return self.symtab[name]
		elif self.superscope is not None:
			return self.superscope.lookup(name)
		else:
			return None

	def bind(self, name, obj, force=False):
		'''
		Bind the name to obj in this scope. If force is False and the name
		is already bound, a KeyError is raised.
		'''
		assert obj is not None
		assert is_legal_identifier(name)
		if not force and name in self.symtab:
			raise KeyError("Name '%s' exists in scope." % name)
		self.symtab[name] = obj


@model
class ModelFactory(Scope):
	'''
	This is a base class for looking up and storing models.

	If successful, this call returns a model object from
	this factory.

	On failure, a KeyError is raised.
	'''

	models = refs()

	def get_model(self, name):
		'''
		Return a model by the given name from this factory.
		'''
		model = self.lookup(name)
		if self.lookup(name) is None:
			src = self.get_model_source(name)
			model = self.compile(src)
			self.bind(name, model)
		return model

	def compile(self, src):
		

	def get_model_source(self, name):
		'''
		This method retrieves the source code of a vectorl model by name.
		It is implemented by subclasses of ModelFactory.
		'''
		raise NotImplemented



@model
class Model(Scope):
	'''
	A model is the result of the translation of a vectorl document
	'''

	factory = ref(inv=ModelFactory.models)

	imports = refs()
	importers = refs(inv=imports)

	declarations = ref_list()

	def __init__(self):
		self.name = None
		self.imports = []

	def add_import(name):
		print('import',name)

	def add_from(model, names):
		print('from',model,'import',*names)



def p_model(p):
	"model : newmodel"
	p[0] = p[1]

def p_newmodel(p):
	"newmodel : "
	p[0] = Model()


def p_model_imports(p):
	"""model : model import_clause
	         | model from_clause """
	p[1].imports.append(p[2])
	p[0] = p[1]

def p_import(p):
	'import_clause : IMPORT ID SEMI'
	p[0] = ('import', p[2])


def p_from_import(p):
	'from_clause : FROM ID IMPORT idlist SEMI'
	p[0] = ('from', p[2], p[4])

def p_idlist(p):
	"""idlist : ID
	         | idlist COMMA ID
	"""
	if len(p)==2:
 		p[0] = [p[1]]
	else:
 		p[0] = p[1]+[p[3]]


parser = yacc.yacc()

if __name__=='__main__':
	result = parser.parse('''
		from foo import a,b;
		import bar;

		import baz;
		''')

	print(result)	
	print(result.imports)
	print(result.declarations)

