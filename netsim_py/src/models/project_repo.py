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

@model
class Entity(Named):
	'''
	A class modeling the entities in the project repository.
	'''
	fields = refs()
	database = ref(inv=Database.entities)
	referents = refs()

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


@model
class Field(Named):
	'''
	A field which is compulsory in the object.
	'''
	entity = ref(inv=Entity.fields)

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
class ApiEntity(Entity):
	'''
	An entity for which the netsim server offers a rest api.
	'''

	# The dao api name. By default, this is 
	# <name>_dao
	dao_name = attr(str, nullable=True)
	CheckedConstraint(LEGAL_IDENTIFIER)(dao_name)

	def __init__(self, name, db, **kwargs):
		super().__init__(name, db)
		self.dao_name = kwargs.get('dao_name', "%s_dao" % name)


# A partial model of the project repository

DB_PT = Database('dpcm_pt_repository')
DB_SIM = Database('dpcm_simulator')

PROJECT = Entity('project', DB_PT)
PLAN = Entity('plan', DB_PT)

NSD = ApiEntity('nsd', DB_SIM)
NSD.add_foreign_key('project_id', PROJECT)
NSD.add_field('plan_id')
NSD.add_field('name')

VECTORL = ApiEntity('vectorl', DB_SIM)
VECTORL.add_foreign_key('project_id', PROJECT)
VECTORL.add_field('name')

SIM = Entity('simoutput', DB_SIM)
SIM.add_foreign_key('nsdid', NSD)

DATABASES = [ DB_PT, DB_SIM ]
ENTITIES = [ PROJECT, PLAN, NSD, VECTORL, SIM ]


#
# models for project repository entity handling
#




@model
class CouchDesign(Named):
	'''
	A CouchEntityModel is a couchdb design document for an entity.
	'''

	# The entity this model is about
	entity = attr(Entity, nullable=False)

	# the views it contains 
	views = refs()

	@property
	def id(self):
		return "_design/"+self.name

	def __init__(self, entity):
		self.entity = entity
		super().__init__("%s_model" % entity.name)

		self.views.add(CouchView('all', entity.idfield))

		for fk in entity.fields:
			if isinstance(fk, ForeignKey):
				self.views.add(CouchView('by_%s' % fk.name, fk))

	def to_object(self):
		ddoc = {
			'_id' : self.id,
			'language' : 'javascript',
			'views' : {}
		}

		for view in self.views:
			ddoc['views'][view.name] = view.to_object()

		return ddoc


@model
class CouchView(Named):
	'''
	A view in a design document.
	'''

	design = ref(inv=CouchDesign.views)

	# when key==null, the view is on doc._id
	key = attr(Field, nullable=True)

	@property
	def resource(self):
		return "%s/_view/%s" % (self.design.id, self.name)

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

