
from models.mf import *
from models.validation import Validation
from models.constraints import is_legal_identifier
import ply.yacc as yacc
from vectorl.lexer import tokens, get_lexer


#
# VectorL model
#

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

    base_lexer = get_lexer()

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
                with V.section("Compilation of model {0}", name):
                    model = self.__compile(name, src)
                if model is None or not V.passed_section():
                    V.fail("Compilation of model {0} failed", name)
                else:
                    self.bind(name, model, force=True)
            if model=='forward':
                V.fail("Cyclical reference for model {0}" % name)
                return None
            return model

    def __compile(self, name, src):
        '''
        Compile the given src object into a new Model object
        and return it.
        '''
        # Create a new lexer
        lexer = self.base_lexer.clone()
        lexer.factory = self
        lexer.modelname = name

        # parse
        model = parser.parse(src, lexer=lexer)

        # validate it
        if model is not None:
            model.validate()

        # done!
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

    def add_event(self, name, args):
        e = Event(self)
        e.args = args
        self.bind(name, e)

    def validate(self):
        pass

@model
class Declaration:
    model = ref(inv=Model.declarations)
    def __init__(self, model):
        self.model = model

@model
class Event(Declaration):
    args = attr(list, nullable=False)



#
# Parser
#

# error handling 
def comperr(p, line, msg, *args, **kwargs):
    lexerr(p.lexer, line, msg, *args, **kwargs)

def lexerr(lex, line, msg, *args, **kwargs):
    V = lex.factory.validation
    name = lex.modelname
    errmsg = msg.format(*args, **kwargs)
    V.failure()
    V.output("error:", "{0}({1}): {2}", name, line, errmsg)

# Rules
def p_error(p):
    if p:
        comperr(p, p.lineno, "Syntax error near {0} token '{1}'", p.type, p.value)
    else:
        raise SyntaxError("Error at end of source")

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
    model = p[0] = p[1]
    if p[2][0]=='import':
        try:
            model.add_import(p[2][1],p[2][2])
        except Exception as e:
            comperr(p, p[2][3], str(e))
    elif p[2][0]=='from':
        try:
            model.add_from(p[2][1], p[2][2])
        except Exception as e:
            comperr(p, p[2][3], str(e))
    else:
        raise RuntimeError('Error in parser at p_model_imports')


def p_import(p):
    'import_clause : IMPORT ID SEMI'
    p[0] = ('import', p[2], p[2], p.lineno(1))

def p_import_as(p):
    'import_clause : IMPORT ID EQUALS ID SEMI'
    p[0] = ('import', p[4], p[2], p.lineno(1))


def p_from_import(p):
    'from_clause : FROM ID IMPORT idlist SEMI'
    p[0] = ('from', p[2], p[4], p.lineno(1))

def p_idlist(p):
    """idlist : ID
             | idlist COMMA ID
    """
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[3]]


# Declarations

def p_arglist_empty(p):
    "arglist : "
    p[0] = list()

def p_arglist(p):
    "arglist : argdefs"
    p[0] = p[1]

def p_argdef(p):
    "argdef : typename ID"
    p[0] = (p[1], p[2])

def p_argdefs(p):
    """argdefs : argdef 
               | argdefs COMMA argdef"""
    p[0] = [p[1]] if len(p)==2 else p[1]+[p[3]]

def p_typename(p):
    """typename : INT 
                | REAL 
                | BOOL"""
    p[0] = p[1]

# events

def p_event_decl(p):
    "event_decl : EVENT ID  LPAREN arglist RPAREN SEMI"
    p[0] = ('event', p[2], p[4], p.lineno(1))


# functions

def p_func_decl(p):
    "func_decl : FUNC typename ID LPAREN arglist RPAREN body "
    p[0] = ('func', p[3], p[2], p[5], p[7], p.lineno(1) )


def p_body(p):
    "body : LBRACE RBRACE "
    pass


# Add to model

def p_model_event_decl(p):
    """model : model event_decl
            | model func_decl
            """
    model = p[0] = p[1]
    try:
        decl = p[2][0]
        if decl == 'event':
            _, ename, eargs, eline = p[2]
            model.add_event(ename, eargs)
        elif decl=='func':
            _, ename, erettype, eargs, ebody, eline = p[2]
            model.add_func(ename, erettype, eargs, ebody)
    except Exception as e:
        comperr(p, eline, str(e))




parser = yacc.yacc()


