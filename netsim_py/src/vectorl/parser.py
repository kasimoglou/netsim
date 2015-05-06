
from models.mf import *
from models.validation import Validation
from models.constraints import is_legal_identifier
import ply.yacc as yacc
from vectorl.lexer import tokens, lexer


@model
class Scope:
    '''An object which defines a new namespace.
    Currently: models, event handlers and functions
    '''
    symtab = attr(dict, nullable=False)
    superscope = ref()
    subscopes = refs(inv=superscope)
    def __init__(self, superscope=None):
        self.symtab = dict()
        self.superscope = superscope

    def lookup(self, name):
        '''Return an object for this name, looking up in this scope
        and its superscope (if any). Return None on failure.
        '''
        if name in self.symtab:
            return self.symtab[name]
        elif self.superscope is not None:
            return self.superscope.lookup(name)
        else:
            return None

    def bind(self, name, obj, force=False):
        '''
        Bind the name to obj in this scope. If force is False and the name
        is already bound, a KeyError is raised.
        '''
        assert obj is not None
        assert is_legal_identifier(name)
        if not force and name in self.symtab:
            raise KeyError("Name '%s' exists in scope." % name)
        self.symtab[name] = obj


@model
class ModelFactory(Scope):
    '''
    This is a base class for looking up and storing models.

    If successful, this call returns a model object from
    this factory.

    On failure, a KeyError is raised.
    '''

    models = refs()

    base_lexer = lexer

    def get_model(self, name):
        '''
        Return a model by the given name from this factory.
        '''
        with self.validation as V:
            model = self.lookup(name)
            if self.lookup(name) is None:
                src = self.get_model_source(name)
                # insert a dummy entry into the symtab, (used to check for cycles)
                self.bind(name, 'forward')
                with V.section("Compiling {0}", name):
                    model = self.__compile(src)
                if model is None:
                    V.fail("Compilation of {0} failed", name)
                else:
                    self.bind(name, model, force=True)
            if model=='forward':
                V.fail("Cyclical reference for model {0}" % name)
                return None
            return model

    def __compile(self, src):
        '''
        Compile the given src object into a new Model object
        and return it.
        '''
        # Create a new lexer
        lexer = self.base_lexer.clone()
        lexer.factory = self

        # parse
        model = parser.parse(src, lexer=lexer)

        # validate it
        model.validate()

        # ok
        if not self.validation.passed():
            return None
        return model


    def get_model_source(self, name):
        '''
        This method retrieves the source code of a vectorl model by name.
        It is implemented by subclasses of ModelFactory.
        '''
        raise NotImplemented

    validation = attr(Validation, nullable=False)

    def __init__(self, validation=None):
        import io
        super().__init__()
        if validation is None:
            self.validation = Validation(outfile=io.StringIO(),max_failures=10000)
        else:
            self.validation = validation




@model
class Model(Scope):
    '''
    A model is the result of the translation of a vectorl document
    '''

    factory = ref(inv=ModelFactory.models)

    imports = refs()
    importers = refs(inv=imports)

    declarations = ref_list()

    def __init__(self, factory):
        super().__init__()
        self.factory = factory

    def __do_import(self, name):
        model = self.factory.get_model(name)
        if model not in self.imports:
            self.imports.add(model)
        return model


    def add_import(self, modelname, name):
        model = self.__do_import(modelname)
        self.bind(name, model)
        return model

    def add_from(self, modelname, names):
        model = self.__do_import(modelname)
        for name in names:
            # note: obj should be searched in symtab, not using model.lookup
            obj = model.symtab[name]
            self.bind(name, obj)

    def validate(self):
        pass

def p_model(p):
    "model : newmodel"
    p[0] = p[1]

def p_newmodel(p):
    "newmodel : "
    p[0] = Model(p.lexer.factory)
    p.lexer.model = p[0]


def p_model_imports(p):
    """model : model import_clause
             | model from_clause """
    model = p[0]=p[1]
    if p[2][0]=='import':
        model.add_import(p[2][1],p[2][2])
    elif p[2][0]=='from':
        model.add_from(p[2][1], p[2][2])
    else:
        raise RuntimeError('Error in parser at p_model_imports')


def p_import(p):
    'import_clause : IMPORT ID SEMI'
    p[0] = ('import', p[2], p[2])

def p_import_as(p):
    'import_clause : IMPORT ID EQUALS ID SEMI'
    p[0] = ('import', p[4], p[2])


def p_from_import(p):
    'from_clause : FROM ID IMPORT idlist SEMI'
    p[0] = ('from', p[2], p[4])

def p_idlist(p):
    """idlist : ID
             | idlist COMMA ID
    """
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[3]]



parser = yacc.yacc()


