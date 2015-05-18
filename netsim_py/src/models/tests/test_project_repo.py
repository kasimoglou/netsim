
import sys, pytest
from models.project_repo import *
from models.mf import validate_classes

def test_validate_pr_metamodel():
	classes = { Named, Database, Entity, Field, ForeignKey, ConstraintUnique,
	ApiEntity, Design, CouchDesign, CouchView, IndexView }
	assert validate_classes(classes,outfile=sys.stdout,detail=20)


#
# Validate
# 

# check that databases are unique
def assert_unique(L):
	L = list(L)
	ll = len(L)
	sl = len(set(L))
	assert ll==sl


def test_validate_pr_model():
	assert_unique(db.name for db in DATABASES)
	for db in DATABASES:
		assert_unique(e.name for e in db.entities)


@pytest.fixture(params=ENTITIES)
def entity(request):
	return request.param

def test_validate_pr_entity(entity):
	if not isinstance(entity, ApiEntity):
		assert_unique(f.name for f in entity.fields)
	else:
		all_names = [f.name for f in entity.fields]+[f.name for f in entity.unique]
		assert_unique(all_names)
		assert_unique(f.primary_key for f in entity.unique)



# To compare javascript code generated, we tokenize it
# This is rather silly, as it does not recognize strings.
# However, it is good enough for now.
def tokeneq(a,b):
	return a.split()==b.split()


def test_object_synopsis():

	ent = Named('foo')
	ent.fields = [Named('bar'), Named('baz')]

	assert tokeneq( gen_object_synopsis(ent, 'X'),
	'''
	{ 
		_id : X._id
		   , bar : X.bar
		   , baz : X.baz
	}
	''')


db = Database('somedb')
foo = Entity('foo', db)
bar = Entity('bar', db)
fk_thebar = ForeignKey('thebar', bar)
foo.fields.add(fk_thebar)

mfoo = CouchDesign(foo)

def test_design():

	assert mfoo.name == "foo_model"
	assert mfoo.id == "_design/foo_model"

	assert len(mfoo.views)==2
	assert { v.name for v in mfoo.views } == { 'all', 'by_thebar' }

	def find(name):
		return [v for v in mfoo.views if v.name==name][0]

	vall = find('all')
	assert vall.name == 'all'
	assert vall.resource == '_design/foo_model/_view/all'

	vby_thebar = find('by_thebar')
	assert vby_thebar.name == 'by_thebar'
	assert vby_thebar.resource == '_design/foo_model/_view/by_thebar'


def test_to_output():

	ddoc = mfoo.to_object()

	edoc = {
		'_id' : '_design/foo_model',
		'language': 'javascript',
		'views' : {
			'all' : {
				'map': gen_map_func(foo, foo.idfield)
			},
			'by_thebar' : {
				'map': gen_map_func(foo, fk_thebar)
			}
		}
	}

	assert ddoc==edoc
