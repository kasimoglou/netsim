'''
This module defines models for a restful api with the project repo.

Created on Sep 17, 2014

@author: vsam
'''


from models.mf import model, attr, ref, refs, ref_list, CheckedConstraint
from models.constraints import  LEGAL_IDENTIFIER, CALLABLE
from collections import namedtuple
from enum import Enum
from numbers import Number
from functools import lru_cache
from simgen.utils import docstring_template

import hashlib, base64, uuid
from urllib.parse import urljoin

#
#  Models for project repository objects
#


@model
class Named:
	name = attr(str, nullable=False)
	CheckedConstraint(LEGAL_IDENTIFIER)(name)

	def __init__(self, name):
		self.name = name

@model
class Database(Named):
	entities = refs()
	design = ref()

@model
class Entity(Named):
	'''
	A class modeling the entities in the project repository.
	'''
	fields = refs()
	database = ref(inv=Database.entities)
	referents = refs()
	design = ref()

	def __init__(self, name, db):
		super().__init__(name)
		self.database = db

		self.idfield = Field('_id')
		self.revfield = Field('_rev')
		self.fields.add(self.idfield)
		self.fields.add(self.revfield)

	def add_foreign_key(self, name, refent):
		fk = ForeignKey(name,refent)
		self.fields.add(fk)
		return fk

	def add_field(self, name):
		field = Field(name)
		self.fields.add(field)
		return field

	def get_field(self, name):
		for f in self.fields:
			if f.name==name:
				return f
		raise KeyError("Field %s not found in entity %s" % (name, self.name))


@model
class Field(Named):
	'''
	A field which is compulsory in the object.
	'''
	entity = ref(inv=Entity.fields)
	constraints = refs()

	def is_key(self):
		return self.name=='_id'

@model
class ForeignKey(Field):
	'''
	A foreign-key field.
	'''
	references = ref(inv=Entity.referents)

	def __init__(self, name, refent):
		super().__init__(name)
		self.references = refent

@model
class FetchField(Named):
	entity =  ref() 					# the entity this belongs to
	fkey = attr(Field, nullable=False)	# the foreign key to use

	def __init__(self, name, fkey, multiple=False):
		super().__init__(name)
		self.fkey = fkey
		self.entity = fkey.entity


@model
class ConstraintUnique(Named):
	'''
	Declare a uniqueness constraint on a number of attributes.
	'''

	entity = ref()
	fields = ref_list(inv=Field.constraints)
	primary_key = attr(bool, default = False)
	def __init__(self, name, entity, keys, primary_key=False):
		super().__init__(name)
		self.entity=entity
		self.primary_key = primary_key
		assert len(keys)>0
		for key in keys:
			if isinstance(key, str):
				key = entity.get_field(key)
			self.fields.append(key)

	def names(self):
		return [f.name for f in self.fields]

@model
class ApiEntity(Entity):
	'''
	An entity for which the netsim server offers a rest api.
	'''

	# The dao api name. By default, this is 
	# <name>_dao
	dao_name = attr(str, nullable=True)
	CheckedConstraint(LEGAL_IDENTIFIER)(dao_name)

	unique = refs(inv=ConstraintUnique.entity)
	primary_key = attr(type=ConstraintUnique, nullable=True, default=None)

	# fetch fields are fields that are added by the server at the API level
	# but not stored in the database. E.g. plan_name for NSDs
	fetch_fields = refs(inv=FetchField.entity)

	# operations supported
	read = attr(bool, nullable=False, default=True)
	create = attr(bool, nullable=False, default=True)
	update = attr(bool, nullable=False, default=True)
	delete = attr(bool, nullable=False, default=True)

	# A callable called to initialize new instances.
	# It is called with parameters (ApiEntity, obj)
	initializer = attr(object, nullable=False)

	def __init__(self, name, db, read_only=False, initializer=(lambda e,x: x),  **kwargs):
		super().__init__(name, db)
		self.dao_name = kwargs.get('dao_name', "%s_dao" % name)

		if read_only:
			self.create = self.update = self.delete = False

		self.initializer = initializer


	def constraint_unique(self, name, *args):
		ConstraintUnique(name, self, args, primary_key=False)

	def set_primary_key(self, *args):
		if self.primary_key is not None:
			raise ValueError("Primary key already exists: %s" % self.primary_key.names())
		self.primary_key = ConstraintUnique("%s_pk" % self.name, self, args, primary_key=True)

	def id_for_primary_key(self, obj):
		assert self.primary_key
		body = ":".join(str(obj[f.name]) for f in self.primary_key.fields)
		return "%s:%s" % (self.name, body)

	def create_id(self, obj):
		if self.primary_key:
			return self.id_for_primary_key(obj)
		else:
			if '_id' in obj:
				return obj['_id']
			else:
				return "%s-%s" % (self.name, uuid.uuid4().hex)

	def initialize(self, obj):
		return self.initializer(self, obj)

	def add_fetch_field(self, name, fkey_name):
		fkey = [f for f in self.fields if isinstance(f, ForeignKey) and f.name==fkey_name]
		if len(fkey)!=1:
			raise ValueError("Cannot determine key field")
		fkey = fkey[0]
		return FetchField(name, fkey)


#
# A partial model of the project repository
# (only entities of concern to us)
#

DB_PT = Database('planning_tool_database')
DB_SIM = Database('netsim_database')
DB_NSLIB = Database('netsim_lib_database')

USER = ApiEntity('user', DB_PT, read_only=True)
USER.add_field('userName')
USER.add_field('userPass')

PROJECT = ApiEntity('project', DB_PT, read_only=True)
PROJECT.add_field('name')
PROJECT.add_field('plans')
PROJECT.add_foreign_key('userId', USER)

PLAN = ApiEntity('plan', DB_PT, read_only=True)
PLAN.add_field('name')

NODEDEF = Entity('nodedef', DB_PT)

NSD = ApiEntity('nsd', DB_SIM)
NSD.add_foreign_key('project_id', PROJECT)
NSD.add_foreign_key('plan_id', PLAN)
NSD.add_field('name')
NSD.set_primary_key('project_id','name')
NSD.add_fetch_field('plan', 'plan_id')


VECTORL = ApiEntity('vectorl', DB_SIM)
VECTORL.add_foreign_key('project_id', PROJECT)
VECTORL.add_field('name')
VECTORL.set_primary_key('project_id','name')

SIM = Entity('simoutput', DB_SIM)
SIM.add_foreign_key('nsdid', NSD)
SIM.add_foreign_key('project_id', PROJECT)
SIM.add_foreign_key('plan_id', PLAN)


# Library entities
NS_NODEDEF = ApiEntity('ns_nodedef', DB_NSLIB, read_only=True)
NS_NODEDEF.add_foreign_key('nodeLib_id', NODEDEF)

NS_COMPONENT = ApiEntity('ns_component', DB_NSLIB, read_only=True)




DATABASES = [ DB_PT, DB_SIM, DB_NSLIB ]
ENTITIES = [ USER, PROJECT, PLAN, NODEDEF, NSD, VECTORL, SIM, NS_NODEDEF, NS_COMPONENT ]




#
# models for project repository entity handling
#


@model
class Design(Named):
	'''
	A couchdb design document.
	'''

	# the views it contains 
	views = refs()

	@property
	def id(self):
		'''The document couchdb id.'''
		return "_design/"+self.name

	def to_object(self):
		ddoc = {
			'_id' : self.id,
			'language' : 'javascript',
			'views' : {}
		}

		for view in self.views:
			ddoc['views'][view.name] = view.to_object()

		return ddoc

	def named_view(self, name):
		"""
		Return the view with the given name, or None if no such
		view exists.
		"""
		for view in self.views:
			if view.name == name:
				return view
		return None



@model
class DbDesign(Design):
	database = ref(inv=Database.design)
	def __init__(self, db, domain=''):
		super().__init__("%s_design")
		self.database=db
	def to_object(self):
		return None

@model
class CouchDesign(Design):
	'''
	A CouchDesign is a couchdb design document for an entity.

	The design document defines one view for each foreign key and
	for each uniqueness constraint.
	'''

	# The entity this model is about
	entity = ref(inv=Entity.design)

	@property 
	def database(self):
		return self.entity.database

	def __init__(self, entity, domain = ''):
		'''
		Create the design document.

		The name of the document is '%s%s_model' %(domain, entity.name).
		Use domain to avoid collisions.
		'''

		self.entity = entity
		super().__init__("%s%s_model" % (domain,entity.name))

		self.views.add(IndexView('all', entity.idfield))

		for fk in entity.fields:
			if isinstance(fk, ForeignKey):
				self.views.add(IndexView('by_%s' % fk.name, fk))


@model
class CouchView(Named):
	'''
	A view in a design document.

	'''
	design = ref(inv=CouchDesign.views)

	@property
	def resource(self):
		return "%s/_view/%s" % (self.design.id, self.name)

@model
class IndexView(CouchView):
	# when key==null, the view is on doc._id
	key = attr(Field, nullable=True)

	@property
	def key(self):
		if self.__key is None:
			self.__key = self.design.entity.idfield
		return self.__key

	def __init__(self, name, key=None):
		super().__init__(name)
		self.__key = key

	def to_object(self):
		return {
			'map' : gen_map_func(self.design.entity, self.key)
		}


@lru_cache(10)
@docstring_template
def gen_object_synopsis(entity, var):
	'''
	{ 
		_id : {{var}}._id
		% for a in entity.fields:
		   , {{a.name}} : {{var}}.{{a.name}}
		% end
	}
	'''
	return locals()


@docstring_template
def gen_map_func(entity, key, value=gen_object_synopsis):
	'''
	function (doc) {
		if(doc.type && doc.type=='{{entity.name}}' {{! "&& doc.%s" % key.name if not key.is_key() else ""}})
			emit(doc.{{key.name}}, {{value(entity, 'doc')}} );
	}	
	'''
	return locals()


MODELS = [CouchDesign(e) for e in ENTITIES if isinstance(e,ApiEntity)]

