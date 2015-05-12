
import pytest
from vectorl.parser import *

from vectorl.tests.modelfactory import *

#
# Tests using the fluent interface to the model
#

@pytest.fixture
def tmf():
	return TestModelFactory()

def test_create_model(tmf):
	model = tmf.add_model('test')
	assert model is tmf.get_model('test')

def test_import_self(tmf):
	model = tmf.add_model('test')
	assert model is tmf.get_model('test')

	model.add_import('test', 'test1')
	assert model['test1'] is model

def test_import_other(tmf):
	model = tmf.add_model('test')
	assert model is tmf.get_model('test')

	model.add_import('sys', 'sys1')
	assert model['sys1'] is tmf.sysmodel

def test_from(tmf):
	model = tmf.add_model('test')
	assert model is tmf.get_model('test')

	model.add_import('sys', 'sys1')
	assert model['sys1'] is tmf.sysmodel

	model.add_from('sys', 'Init')
	assert model['Init'] is tmf.sysmodel['Init']

def test_add_action(tmf):
	modelA = tmf.add_model('A')
	modelB = tmf.add_model('B')
	modelB.add_import('A', 'A')

	E = modelA.add_event('E',[('int','a')])
	A = modelB.add_action(E, PrintStatement())

	assert A.event is E
	assert A.model is modelB


