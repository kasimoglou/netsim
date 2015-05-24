#
# This is part of the VectorL python runtime engine.
# These are the models for types.
# It is based on numpy.
#

import numpy as np
from models.mf import *
from simgen.utils import docstring_template

#
# Types: We use types declared by numpy.
#  
#

@model
class TypeInfo:
    '''
    Model for a VectorL type.
    '''

    name = attr(str, nullable=False)
    pytype = attr(type, nullable=False)
    make = attr(object, nullable=False)
    dtype = attr(np.dtype, nullable=False)
    rank = attr(int, nullable=False)

    def __init__(self, name, pytype, make, rank):
        self.name = name
        self.pytype = pytype
        self.make = make
        self.dtype = make([0]).dtype #numpy type
        self.rank=rank

    @staticmethod
    def forLiteral(x):
        '''
        Find the type for a literal
        '''
        for T in TYPES:
            if isinstance(x, T.pytype): return T
        return OBJ

    @staticmethod
    def forType(t):
        return TypeInfo.bytype[t]

    @staticmethod
    def forName(n):
        return TypeInfo.byname[n]

    def auto_castable(self, T):
        return self.rank <= T.rank

    def __call__(self, value):
        return self.make(value)

    def __str__(self):
        return self.name
    def __repr__(self):
        return "TypeInfo('%s')" % self.name

# static members
BOOL = TypeInfo('bool', bool, np.bool_, 1)
INT = TypeInfo('int', int, np.int_, 2)
REAL = TypeInfo('real', float, np.float_, 3)
TIME = TypeInfo('time', float, np.float_, 4)

# Real types
TYPES = (BOOL, INT, REAL, TIME)

# This pseudo-type is used to manipulate internal data. There are no
# variables of this type, only intermediate results.
OBJ = TypeInfo('object', object, lambda x: np.array(x, dtype=object),5)
ALL_TYPES = TYPES+(OBJ,)

# Maps used to translate between type systems
TypeInfo.byname = {t.name : t for t in TYPES}
TypeInfo.bytype = {t.dtype : t  for t in TYPES if t is not TIME}


