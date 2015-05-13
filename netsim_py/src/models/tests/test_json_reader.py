
from models.mf import *
from models.json_reader import *
import pytest
import json, logging



@model
class Foo:
	one = ref()
	descend(one)

	many = refs()
	descend(many)

	ordered = ref_list()
	descend(ordered)

	type= attr(str)

@model
class Bar:
	parent = ref(inv=Foo.one)
	type = attr(str)
	no = attr(int)

@model
class Baz:
	parent = ref(inv=Foo.many)
	
	type = attr(str)
	required(type)

	number = attr(int)
	json_name('no')(number)


@model
class Rag:
	parent = ref(inv=Foo.ordered)
	type = attr(str)

	no = attr(int, default=10)
	ignore(no)

json_txt = '''
{
	"type": "foo",
	"one" : { "type":  "bar" },
	"many" : [ {"type": "baz", "no": 1 }, {"type": "baz", "no": 2 } ],
	"ordered" : [ {"type":"rag", "no":1 }, {"type": "rag", "no":2 } ]
}
'''

def test_json_reader_descend():
	json_obj = json.loads(json_txt)

	jr = JSONReader(logging.root)
	foo = Foo()
	jr.populate_modeled_instance(foo, json_obj)

	assert ignore.has(Rag.__model_class__.get_attribute('no'))

	assert foo.type == 'foo'
	assert foo.one.type=='bar'
	assert len(foo.ordered)==2

	foomany = list(foo.many)
	assert len(foomany)==2
	assert foomany[0].type=='baz'
	assert foomany[0].number in (1,2)
	assert foomany[1].type=='baz'
	assert foomany[1].number in (1,2)

	assert foo.ordered[1].no == 10


def test_json_reader_require():

	jr = JSONReader(logging.root)
	baz = Baz()

	json_obj = json.loads('''{ "no": 4}''')
	with pytest.raises(RequiredMissingError):
		jr.populate_modeled_instance(baz, json_obj)

