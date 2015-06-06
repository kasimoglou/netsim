'''
	Application Authentication & Authorization

	This code works together with 'models.aaa'.
	Mostly code to manage beaker sessions and
	caching.

	@author: vsam
'''

from bottle import request, redirect
import logging

import runner.apierrors as apierrors
from runner.monitor import Manager
from models.aaa import *

#
# Authentication
#

logger = logging.getLogger('auth')

def session():
	'''
	Return the beaker session object.
	'''
	return request.environ.get('beaker.session')


def set_current_user(user):
	'''
	Set the current user.
	'''
	session()['user'] = user
	session().save()


def current_user():
	'''
	Return the current user, or None.
	'''
	return session().get('user', None)

def current_user_is_admin():
	'''
	Return True iff current user is an administrator.
	'''
	cu = current_user()
	if cu is not None:
		user = Manager.get_user(cu)
		assert isinstance(user, User)
		return user.is_admin

def clear_current_user():
	if current_user() is not None:
		logger.info('User %s logged out', current_user())
		del session()['user']
	session().save()


# dpcm login

def current_dpcm_user():
	return session().get('dpcm_user', None)

def set_dpcm_user(user):
	session()['dpcm_user'] = user
	session().save()
	logger.info("DPCM user %s logged in", user)

def clear_dpcm_user():
	if current_dpcm_user() is not None:
		del session()['dpcm_user']

#
# Authorization
#

def session_roles():
	'''
	Return a set of roles for the current session.
	'''
	roles = { Anyone }

	user = current_user()
	if user is not None:
		roles.add(LoggedIn)
	if current_user_is_admin():
		roles.add(Admin)

	dpcm_user = current_dpcm_user()
	if dpcm_user is not None:
		roles.add(DpcmUser)

	return roles


#
# A 'privilege' is a function returning boolean
#

def require_privilege(priv, on_fail=None, throw=apierrors.Forbidden, **extra_args):
	'''Return a decorator for the given privilege'''
	import functools

	assert on_fail is None or callable(on_fail)
	assert throw is None or issubclass(throw, Exception)

	def auth_decorator(f):
		@functools.wraps(f)
		def auth_wrapper(*args, **kwargs):
			# check privilege
			if not priv():
				if on_fail is not None:
					on_fail(**extra_args)
				else:
					raise throw()

			# call the function
			return f(*args, **kwargs)
		return auth_wrapper
	return auth_decorator


logged_in = require_privilege(lambda : current_user() is not None, 
	on_fail=lambda : redirect('/admin/login.html') )

