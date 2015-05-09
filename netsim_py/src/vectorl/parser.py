
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
            if model is None:

                # May throw
                src = self.get_model_source(name)

                # insert a dummy entry into the symtab, (used to check for cycles)
                self.bind(name, 'forward')
                with V.section("Compilation of model {0}", name):
                    model = self.__compile(name, src)
                if model is None or not V.passed_section():
                    V.fail("Compilation of model {0} failed", name)
                else:
                    self.bind(name, model, force=True)
            elif model=='forward':
                V.fail("Cyclical reference for model {0}" % name)
                model = None
            return model

    def __compile(self, name, src):
        '''
        Compile the given src object into a new Model object
        and return it.
        '''
        ast = self.__parse(name, src)
        if ast is None:
            return None
        model = self.__transform(name, ast)

        # done!
        return model

    def __parse(self, name, src):
        # Create a new lexer
        lexer = self.base_lexer.clone()
        lexer.factory = self
        lexer.modelname = name

        # parse
        ast = parser.parse(src, lexer=lexer)
        return ast

    def __transform(self, name, ast):
        '''
        Return an uninitialized model, with its namespace augmented by imports.
        Subclasses can augment this model with more information.
        '''
        model = Model(self)
        model.ast = ast
        for clause in ast:
            if clause[0] == 'import':
                model.add_import(clause[1], clause[2])
            elif clause[0]=='from':
                model.add_from(clause[1], clause[2])
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
    ast = attr(list)
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

    def add_event(self, name, params):
        e = Event(self)
        e.params = params
        self.bind(name, e)

    def add_function(self, name, rtype, params, body):
        e = Function()
        e.rtype = rtype
        e.params = params
        e.body = body
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
    '''
    An event is emitted from event handlers, 
    or from the environment.
    '''
    params = attr(list, nullable=False)
    handlers = refs()

@model
class Action(Declaration):
    '''
    A template for event handlers for events of
    a particular type.
    '''
    pass

@model
class EventHandler(Declaration):
    '''
    An event handler is executed to process an event.    
    '''
    event = ref(inv=Event.handlers)
    body = ref()


@model
class Function(Declaration):
    '''A template for creating formulas.'''
    rtype = attr(str, nullable=False)
    params = attr(list, nullable=False)
    body = ref()


@model
class Formula(Declaration):
    '''
    A formula is an encapsulation of an expression.
    '''
    rtype = attr(str, nullable=False)
    expr = ref()

@model
class Const(Formula):
    value = attr(object)

@model
class Variable(Declaration):
    pass



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

# Model declaration

def p_model(p):
    "model : newmodel"
    p[0] = p[1]

def p_newmodel(p):
    "newmodel : "
    p[0] = []
    p.lexer.model = p[0]


def p_model_imports(p):
    """model : model import_clause
             | model from_clause 
             | model event_decl 
             | model func_decl 
             | model fexpr_decl
             | model var_decl
             | model action_decl
            """
    p[0] = p[1]+[p[2]]

# importing other models

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


# Argument declarations (for functions and event types)

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
                | BOOL
                | TIME """
    p[0] = p[1]


# event type

def p_event_decl(p):
    "event_decl : EVENT ID  LPAREN arglist RPAREN SEMI"
    p[0] = ('event', p[2], p[4], p.lineno(1))


# functions

def p_func_decl(p):
    "func_decl : FUNC typename ID LPAREN arglist RPAREN body "
    p[0] = ('func', p[3], p[2], p[5], p[7], p.lineno(1) )


def p_body(p):
    "body : LBRACE declarations RBRACE "
    p[0] = p[2]


def p_declarations(p):
    """ declarations : 
                     | declarations fexpr_decl
                  """
    if len(p)==1:
        p[0] = []
    else:
        p[0] = p[1]+[p[2]]

# inline functions

def p_fexpr_decl(p):
    """ fexpr_decl : typename ID EQUALS expression SEMI """
    p[0] = ('fexpr', p[2],p[1],p[4])

def p_cexpr_decl(p):
    """ fexpr_decl : CONST typename ID EQUALS expression SEMI """
    p[0] = ('const', p[3],p[2],p[5])

# variables

def p_var_decl(p):
    """ var_decl : VAR typename ID EQUALS expression SEMI """
    p[0] = ('var', p[3], p[2], p[5])

# actions

def p_event_action(p):
    """ action_decl : ON ID LBRACE action_block RBRACE """
    p[0] = ('action', p[2], p[4])

def p_action_block(p):
    """ action_block : statement
                     | action_block statement """
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

# statements (allowed in action blocks)

def p_emit_statement(p):
    " statement : EMIT ID LPAREN expr_list_opt RPAREN AFTER expression SEMI "
    p[0] = ('emit', p[2],p[4],p[7])

def p_assignment(p):
    " statement : expression ASSIGN expression SEMI "
    p[0] = ('assign', p[1], p[3])

def p_fexpr_statement(p):
    " statement : fexpr_decl "
    p[0] = p[1]

def p_if_statement(p):
    """ statement : IF LPAREN expression RPAREN THEN statement 
                  | IF LPAREN expression RPAREN THEN statement ELSE statement
    """
    assert len(p) in (7,9)
    if len(p)==7:
        p[0] = ('if', p[3], p[6], None)
    else:
        p[0] = ('if', p[3], p[6], p[8])


#
# Expression grammar
#

def p_primary_expression_literal(p):
    """ primary_expression : ICONST 
                            | FCONST 
                            | TRUE 
                            | FALSE  """
    p[0] = ('literal', p[1])

def p_primary_expression_id(p):
    """ primary_expression :  qual_id """
    p[0] = p[1]

def p_qual_id(p):
    """ qual_id : ID 
                | ID PERIOD ID """
    if len(p)==4:
        p[0] =  ('id', p[1],p[3])
    else:
        p[0] = ('id', None, p[1])

def p_primary_expression_paren(p):
    """ primary_expression :  LPAREN expression RPAREN  """
    p[0] =  p[2]

def p_primary_expression_concat(p):
    """ primary_expression : LBRACKET expr_list_opt RBRACKET """
    p[0] = ('concat', p[2])

def p_primary_expression_fcall(p):
    """ primary_expression : qual_id LPAREN expr_list_opt RPAREN """
    p[0] = ('fcall', p[1], p[3])

def p_expr_list_empty(p):
    """ expr_list_opt : 
                      | expr_list """
    if len(p)==1:
        p[0] = []
    else:
        p[0] = p[1]

def p_expr_list(p):
    """ expr_list : expression 
                  | expr_list COMMA expression """
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[3]]

def p_postfix_expression(p):
    """ postfix_expression : primary_expression 
                           | postfix_expression LBRACKET index_spec RBRACKET """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('index', p[1], p[3])

def p_index_spec(p):
    """ index_spec : index_seq 
                   | index_seq COMMA ELLIPSIS 
                   | ELLIPSIS 
                   | ELLIPSIS COMMA index_seq """
    assert len(p) in (2,4)
    if len(p)==2:
        if p[1]=='ELLIPSIS':
            p[0] = ['...']
        else:
            p[0] = p[1]
    else:
        if p[1]=='ELLIPSIS':
            p[0] = ['...']+p[3]
        else:
            p[0] = p[1]+['...']


def p_index_seq(p):
    """ index_seq : index_op 
                  | index_seq COMMA index_op """
    if len(p)==2:
        p[0] = [p[1]]
    else:
        p[0] = p[1]+[p[3]]

def p_index_op_index(p):
    " index_op : expression "
    p[0]=('pos', p[1])

def p_index_op_range(p):
    " index_op : expr_opt COLON expr_opt"
    p[0] = ('range', p[1],p[3])

def p_expr_opt(p):
    """ expr_opt : 
                 | expression """
    assert len(p) in (1,2)
    if len(p)==1:
        p[0] = None
    else:
        p[0] = p[1]

def p_index_op_newdim(p):
    " index_op : SUB "
    p[0] = '_'

def p_unary_expression(p):
    """ unary_expression : postfix_expression 
        | unary_op cast_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('unary', p[1], p[2])

def p_unary_op(p):
    """ unary_op : PLUS 
                | MINUS 
                | LNOT """
    p[0] = p[1]

def p_cast_expression(p):
    """ cast_expression : unary_expression 
                    | LPAREN typename RPAREN cast_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('cast', p[2], p[4])

def p_mult_expression(p):
    """ mult_expression : cast_expression 
                    | mult_expression mult_op cast_expression """ 
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])


def p_mult_op(p):
    """ mult_op : TIMES 
                | DIVIDE 
                | MOD """
    p[0] = p[1]

def p_add_expression(p):
    """ add_expression : mult_expression 
                       | add_expression add_op mult_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])

def p_add_op(p):
    """ add_op : PLUS 
               | MINUS """
    p[0] = p[1]

def p_shift_expression(p):
    """ shift_expression : add_expression 
                         | shift_expression shift_op add_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])

def p_shift_op(p):
    """ shift_op : LSHIFT 
                 | RSHIFT """
    p[0] = p[1]

def p_rel_expression(p):
    """ rel_expression : shift_expression 
                        | rel_expression rel_op shift_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])

def p_rel_op(p):
    """ rel_op : LT 
                | GT 
                | LE 
                | GE """
    p[0] = p[1]

def p_eq_expression(p):
    """ eq_expression : rel_expression 
                    | eq_expression eq_op rel_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])

def p_eq_op(p):
    """ eq_op : EQ 
                | NE """
    p[0] = p[1]

def p_and_expression(p):
    """ and_expression : eq_expression 
                    | and_expression AND eq_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])

def p_xor_expression(p):
    """ xor_expression : and_expression 
                    | xor_expression XOR and_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])

def p_or_expression(p):
    """ or_expression : xor_expression 
                    | or_expression OR xor_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])

def p_expression(p):
    """ expression : or_expression 
                    | or_expression CONDOP expression COLON expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('cond', p[1], p[3], p[5])







parser = yacc.yacc()


