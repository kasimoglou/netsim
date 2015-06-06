'''
	Models for Application Authentication and Authorization
'''

from models.mf import model, attr, ref, refs, ref_list, CheckedConstraint
from models.constraints import Constraint

#
# Authentication
#

def is_legal_user_name(name):
    import re
    return bool(isinstance(name, str) and re.match("[A-Za-z][_@\.a-zA-Z0-9]*$",name)\
     	and (1 <= len(name) <= 24))
LEGAL_USER_NAME = Constraint(is_legal_user_name, "is legal user name")


@model
class User:
	username = attr(str, nullable=False)
	CheckedConstraint(LEGAL_USER_NAME)(username)

	password = attr(str)
	is_admin = attr(bool,nullable=False, default=False)

	def __init__(self, username, password, is_admin):
		self.username = username
		self.password = password
		self.is_admin = is_admin

	def __repr__(self):
		return "User(%s)" % (self.username+"[admin]" if self.is_admin else self.username)

#
# Base class for authorization entities
# 

@model
class Named:
	name = attr(str, nullable=False)
	def __init__(self, name):
		self.name = name
		self.add_instance(self)
		self.implies.add(self)

	# An 'implies' relationship,
	# which is reflexive and transitive
	implies = refs()
	implied_by = refs(inv=implies)

	#
	# a <<== b  means "declare that b implies a" 
	#
	def __ilshift__(self, other):
		for p in self.implies:
			for q in other.implied_by:
				p.implied_by.add(q)
		return self

	@classmethod
	def add_instance(cls, obj):
		if not hasattr(cls, 'by_name'):
			cls.by_name = {}
		cls.by_name[obj.name] = obj
	def __repr__(self):
		return "%s(%s)" % (self.__class__.__name__, self.name)


#
#  Roles
#

@model
class Role(Named):
	'''
	Represent roles w.r.t entity classes
	'''
	pass
	def __init__(self, name):
		super().__init__(name)
		global Anyone
		if Anyone is not None:
			Anyone <<= self

# This is the 'any user' role (unauthenticated users)
Anyone = None
Anyone = Role('anyone')

# 'Owner' of an entity (the semantics are entity-specific)
Owner = Role('owner')

# Refers to DPCM users
DpcmUser = Role('user')
ProjectEnabled = Role('project_enabled_user')

# refers to a backend user
Admin = Role('admin')
LoggedIn = Role('loggedIn') 



#
# Privileges
#

@model
class Privilege(Named):
	'''
	Represent operations on entities of a class
	'''
	eclass = refs()

	def __init__(self, name):
		# set name and make everything included in the All
		# privilege
		super().__init__(name)
		global All
		if All is not None:
			self <<= All

# All privileges
All = None  # this is needed!
All = Privilege('ALL')

# for objects
Create = Privilege('create')
Read = Privilege('read')
Update = Privilege('update')
Delete = Privilege('delete')

# for collections
Query = Privilege('query')

# for the server
Browse = Privilege('browse')

CreateUser = Privilege('create_user')
DeleteUser = Privilege('delete_user')
ChangeUserPassword = Privilege('change_user_password')
ChangeAdminStatus = Privilege('change_user_admin_status')

Shutdown = Privilege('shutdown')

#
# Access Contol Lists
# 


@model
class ACEntry:
	'''Access control entry'''
	acl = ref()
	allow = attr(bool, nullable=False, default=True) # allow or deny
	role = attr(Role, nullable=False)
	priv = attr(Privilege, nullable=False)

	def __init__(self, role, priv, allow=True):
		self.allow = allow
		self.role = role
		self.priv = priv

	def matches(self, roles, priv):
		return priv in self.priv.implies and self.role in roles


@model
class ACL:
	eclass = ref()
	rules = ref_list(inv=ACEntry.acl)
	def allow(self, role, priv):
		self.rules.append(ACEntry(role, priv,True))
	def deny(self, role, priv):
		self.rules.append(ACEntry(role, priv,False))
	def match(self, roles, priv):
		for rule in self.rules:
			if rule.matches(roles, priv):
				return rule.allow  # return first matching rule!
		return None


@model
class EClass(Named):
	'''
	A collection of entities with common privileges
	'''
	by_name = {}
	
	acl = ref(inv=ACL.eclass)
	privileges = refs(inv=Privilege.eclass)
	superclass = ref()
	subclasses = refs(inv=superclass)

	def __init__(self, name, superclass=None):
		super().__init__(name)
		if superclass is None:
			self.superclass = AnyEntity
		else:
			self.superclass = superclass
		self.acl = ACL()

	def __check_acl(self, roles, priv):
		d = self.acl.match(roles, priv)
		if d is None and self.superclass is not None:
			d = self.superclass.__check_acl(roles, priv)
		if d is None: d = False
		return d

	def authorize(self, roles, priv):
		'''The main method used to determine authorization.'''
		all_roles = set()
		for role in roles:
			all_roles.update(role.implies)
		return self.__check_acl(all_roles, priv)


	def allow(self, role, priv): self.acl.allow(role, priv)
	def deny(self, role, priv): self.acl.deny(role, priv)

#
#  Entity class hierarchy
#

AnyEntity = None
AnyEntity = EClass('any_entity')

PrEntity = EClass('project_repo_entity')

PT_Entity = EClass('pt_entity',PrEntity)
ProjectEntity = EClass('project_item', PT_Entity)
Project = EClass('project', ProjectEntity)
Plan = EClass('plan', ProjectEntity)

DT_Entity = EClass('dt_entity', PrEntity)
Nsd = EClass('NSD', DT_Entity)
Simulation = EClass('Simulation', DT_Entity)
VectorL = EClass('VectorL', DT_Entity)


Server = EClass('server')
UserRecord = EClass('user')


#############################################
#
# Current policy
#
#############################################

# default rules to deny everything to all, unless he is admin
AnyEntity.allow(Admin, All)
AnyEntity.deny(Anyone, All)

#####################
# Project repository
#####################

# For now allow everyone every right on the repository
# N.B. Change allow to deny to make more specific rules apply
PrEntity.allow(Anyone, All)

PrEntity.allow(Owner, Create) # 'Owner' refers to project owner
PrEntity.allow(Owner, Read)  
PrEntity.allow(Owner, Update)
PrEntity.allow(Owner, Delete)

PrEntity.allow(ProjectEnabled, Create) # 'Owner' refers to project owner
PrEntity.allow(ProjectEnabled, Read)  
PrEntity.allow(ProjectEnabled, Update)
PrEntity.allow(ProjectEnabled, Delete)


PT_Entity.allow(DpcmUser, Query)
DT_Entity.allow(DpcmUser, Query)


####################
# NetSim server
####################

UserRecord.allow(Owner, ChangeUserPassword)


