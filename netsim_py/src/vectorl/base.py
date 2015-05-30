
import sys
import logging
import models.validation as val
from models.mf import model, attr

#
# Source location tracking
#

class AstNode(tuple):
    def __repr__(self):
        return "AstNode"+super().__repr__()+ ":%d:" % self.lineno +"[%d,%d]"%self.linespan


#
# Base for model
#

@model
class SourceItem:
    '''
    Base class for vectorl model classes.
    '''

    ast = attr(AstNode, nullable=True, default=None)

    @property
    def lineno(self):
        return self.ast.lineno if self.ast is not None else "??"

    @property
    def model_name(self):
        return self.ast.model_name if self.ast is not None else "<unknown model>"
    
    @property
    def origin(self):
        return "%s(%s)" % (self.model_name, self.lineno)

    def description(self):
        return "%s" % self.__class__.__name__
    
    def __repr__(self):
        return "%s at %s" % (self.description(), self.origin)


#
# Tracking
#

class CompilerErrorLine(logging.Formatter):
	def format(self, record):
		if hasattr(record, 'ast'):
			ast = record.ast
			model = ast.model_name
			line = ast.lineno
			return "%s(%s): %s" % (model, line, record.getMessage())
		else:
			return super().format(record)

class AstHandler(logging.StreamHandler):
	def __init__(self, stream=sys.stderr):
		super().__init__(stream)
		self.setFormatter(CompilerErrorLine())


class Compiler(val.Process):
	def __init__(self, name=None):
		super().__init__(name=name, logger=logging.getLogger('vectorl'))
		self.addScopeHandler(AstHandler())

class AstContext(val.Context):
	def __init__(self, ast):
		super().__init__(ast=ast)




