'''
	@author: vsam
'''

from runner import api
from runner import dpcmrepo
import pytest
from setup_repo import clone
from models.project_repo import *



# Clone a new local repository for running the tests
@pytest.fixture(scope='module')
def repo(request):
	# Clear the repository
	dpcmrepo.initialize_repo()
	repo = dpcmrepo.repo()
	try:
		# remove a stale test database
		dpcmrepo.repo().delete(DB_TEMP.name)
	except dpcmrepo.NotFound:
		pass
	return repo

DB_TEMP = Database('temp')
FOO = ApiEntity('foo', DB_TEMP)
FOO.add_foreign_key('myproject', PROJECT)
FOO.add_foreign_key('mynsd', NSD)
FOO.add_foreign_key('mysim', SIM)

mFOO = CouchDesign(FOO)

# Create a fictitious type 'foo' to test the dao
@pytest.fixture
def foo_dao(request, repo):
	# load the view designs in the repo
	repo.DB = repo.create(DB_TEMP.name)
	def fin():
		repo.delete(DB_TEMP.name)
		del repo.DB
	request.addfinalizer(fin)
	repo.create_models([mFOO])
	return api.RepoDao(mFOO)

def check_create(repo, foo_dao, obj_body):
	obj = foo_dao.create(obj_body)
	assert '_id' in obj
	assert 'type' in obj and obj['type']=='foo'
	for k in obj_body:
		assert obj[k]==obj_body[k]

	sobj = repo.DB.get(obj['_id'])
	assert sobj==obj
	return obj


def test_crud_create(repo, foo_dao):
	check_create(repo, foo_dao, {'name':'Vasilis'})
def test_crud_create_empty(repo, foo_dao):
	check_create(repo, foo_dao, {})
def test_crud_create_big(repo, foo_dao):
	check_create(repo, foo_dao, 
		{ ("label%d" % n) : { "value": n*n, "index" : n }  
		for n in range(10) })
def test_crud_create_given_key(repo, foo_dao):
	obj = check_create(repo, foo_dao, { '_id': "foo032" })
	assert obj['_id']=="foo032"

# errors
def test_create_errors(repo, foo_dao):
	with pytest.raises(api.BadRequest):
		foo_dao.create({'type': 'bar'})['type']=='foo'
	with pytest.raises(api.Error):
		foo_dao.create({'_id': 10 })

# Get
def test_get(repo, foo_dao):
	# iterate over repo
	for obj in repo.DB.all():
		if '_id' not in obj:
			print(obj)
			continue
		if obj.get('type',None)=='foo':
			obj2 = foo_dao.read(obj['_id'])
			assert obj==obj2
		else:
			with pytest.raises(api.Error):
				foo_dao.read(obj['_id'])

	# check for phony id
		with pytest.raises(api.Error):
			foo_dao.read(obj['_id'])


def test_update(repo, foo_dao):
	obj = foo_dao.create({ 'value':1 })
	assert obj['value']==1
	print(obj)

	# check that the correct update works
	oid = obj['_id']
	obj['value'] = 2
	obj2 = foo_dao.update(oid, obj)
	print("send=",obj,"receive=",obj2)

	# Check for conflict
	with pytest.raises(api.Conflict):
		obj2 = foo_dao.update(oid, obj)

	del obj['_rev']
	with pytest.raises(api.Conflict):
		foo_dao.update(oid, obj)


	# check for correct update
	obj2['value'] = 2
	obj3 = foo_dao.update(oid, obj2)

	assert obj3['value']==2


def test_delete(repo, foo_dao):
	obj = foo_dao.create({ 'value':1 })
	assert obj['value']==1

	# check that the correct update works
	oid = obj['_id']

	# Check for val
	foo_dao.delete(oid)
	with pytest.raises(api.NotFound):
		foo_dao.read(oid)

	# re-create
	obj2 = foo_dao.create({ '_id': oid })
	assert 'value' not in obj2

	obj2['value'] = 4
	obj3 = foo_dao.update(oid, obj2)

	assert obj3['value']==4


@pytest.fixture
def sample(foo_dao):
	# create a bunch of objects
	print('CREATE SAMPLE')
	samples = []
	for i in range(20):
		obj = {
			'index': i,
			'myproject': 'PRJ_%d' % (i/5),
			'mynsd': 'NSD_%d' % (i/2)
		}
		if i%3==0:
			obj['mysim'] = 'SIM_%d' % (i%2)
		obj = foo_dao.create(obj)
		samples.append(obj)
	return samples


def test_find(repo, foo_dao, sample):
	assert len(sample)==20
	s = foo_dao.findAll(reduced=False)
	
	s1 = sorted(s, key=lambda x: x['_id'])
	s2 = sorted(sample, key=lambda x: x['_id'])
	assert len(s1)==len(s2)

	for i in range(len(s1)):
		assert s1[i]==s2[i]

	for obj in foo_dao.findAll():
		assert 'index' not in obj

	s = list(foo_dao.findBy('by_mynsd'))
	assert len(s)== 20

	s = list(foo_dao.findBy('by_mynsd', key='NSD_3', reduced=False))
	assert len(s) == 2
	assert all(obj['index'] in range(6,8) for obj in s)

	s = list(foo_dao.findBy('by_myproject', key='PRJ_3', reduced=False))
	assert len(s) == 5
	assert all(obj['index'] in range(15,20) for obj in s)

	s = list(foo_dao.findBy('by_mysim', key='SIM_0', reduced=False))
	sidx = [i for i in range(20) if i%3==0 and i%2==0]
	assert len(s) == len(sidx)
	assert all(obj['index'] in sidx for obj in s)

