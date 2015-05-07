
import pytest, io
from vectorl.parser import ModelFactory, Model
from models.validation import Validation

class TestModelFactory(ModelFactory):
	'''
	A simple implementation of ModelFactory, for testing.
	'''
	def __init__(self, sources=[], validation=None):
		super().__init__(validation=validation)
		self.sources = dict()
		for name, src in sources:
			self.add_source(name, src)

	def add_source(self, name, src):
		self.sources[name]  = src

	def get_model_source(self, name):
		return self.sources[name]

MF1 = [
	('foo', ""),
	('bar', "import foo;")
]

MF2 = MF1+[
	('baz', """
	import bar;
	from bar import foo;
	import foo1 = foo;
	import foo2 = foo;
		""")
]

def test_parse_imports():
	tmf = TestModelFactory(sources=MF1)

	bar = tmf.get_model('bar')
	assert tmf.validation.passed()

	assert isinstance(bar, Model)
	assert len(bar.imports)==1
	foo = tmf.get_model('foo')

	assert foo in bar.imports
	print('\n',tmf.validation.outfile.getvalue())

def test_parse_imports2():
	tmf = TestModelFactory(sources=MF2)
	baz = tmf.get_model('baz')
	assert tmf.validation.passed()
	assert 'foo' in tmf.symtab
	assert 'bar' in tmf.symtab
	assert tmf.symtab['foo'] is baz.symtab['foo1']
	assert tmf.symtab['foo'] is baz.symtab['foo2']
	print('\n',tmf.validation.outfile.getvalue())

BADMF1 = MF2 + [
('bad', """
	import foo;
	import foo;
	""")
]

BADMF2 = MF2 + [
('bad', """
	import foo1 = foo;
	import foo1 = foo;
	""")
]


BADMF3 = MF2 + [
('bad1',"""
	import foo1 = foo;
	import foo1 = foo;
	"""),
('bad', """
	import foo1 = foo;
	import bad1;
	""")
]



@pytest.fixture(params=[BADMF1, BADMF2, BADMF3,
	[('bad', "@lexerror")],
	[('bad', ";")],
	[('bad', "garba g e  inthetext")],
	[('bad', "import foo")]
	])
def import_errors(request):
	return request.param

def test_parse_import_error(import_errors):
	with Validation(outfile=io.StringIO()) as val:
		tmf = TestModelFactory(import_errors, val)
		model = tmf.get_model('bad')

	assert not val.passed()
	print('\n',tmf.validation.outfile.getvalue())


@pytest.fixture(params=[
	('evt', "event foo();"),
	('evt', "event foo(int a);"),
	('evt', "event foo(real x);"),
	('evt', "event foo(bool p);"),
	('evt', "event foo(bool a, bool b, real x );")
	])
def event_decl(request):
	return request.param

def test_event_decl(event_decl):
	with Validation(outfile=io.StringIO()) as val:
		tmf = TestModelFactory(sources=[event_decl], validation=val)
		model = tmf.get_model('evt')
	print(tmf.validation.outfile.getvalue())
	assert tmf.validation.passed()



