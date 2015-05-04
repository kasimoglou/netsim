'''
	Application Authentication & Authorization

	@author: vsam
'''

from bottle import request, redirect
from runner import api
import logging

#
# Authentication
#

_logger = None
def logger():
	global _logger
	if _logger is None:
		_logger = logging.getLogger('auth')
	return _logger


def session():
	return request.environ.get('beaker.session')

def login(user, password):
	# No password at this time
	success = user and ' ' not in user
	if success:
		session()['user'] = user
		session().save()
		logger().info('User %s logged in', user)
	else:
		logger().info('Login failure')
	return success


def current_user():
	return session().get('user', None)


def logout():
	if current_user() is not None:
		logger().info('User %s logged out', current_user())
		del session()['user']
	session().save()



#
# Authorization
#



def authorize(role, privilege, entity):
	'''
	Return a boolean value indicating whether the given
	role has a privilege on an entity.
	'''
	return True




#
# A privilege is a function returning boolean
#

def require_privilege(priv, on_fail=None, throw=api.Forbidden, **extra_args):
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

