
from models.mf import *
from models.constraints import is_legal_identifier, LEGAL_IDENTIFIER
import ply.yacc as yacc
from vectorl.lexer import tokens, get_lexer
from collections import namedtuple

from vectorl.expr import *

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
    declarations = ref_list()

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

    def __contains__(self, key):
        return self.lookup(key) is not None

    def bind(self, name, obj, force=False):
        '''
        Bind the name to obj in this scope. If force is False and the name
        is already bound, a KeyError is raised.
        '''
        if obj is None:
            raise ValueError("Illegal attempt to bind None to a name")
        if not is_legal_identifier(name):
            raise KeyError("Name {0} is not a legal identifier".format(name))
        if not force and name in self.symtab:
            raise KeyError("Name '%s' bound in scope." % name)
        self.symtab[name] = obj

    def binds(self, name):
        return name in self.symtab

    def __getitem__(self, name):
        # reimplement to get qualified names
        if isinstance(name, tuple):
            scope = self
            for n in name:
                assert isinstance(scope, Scope)
                scope = scope[n]
            return scope
        else:
            seq = name.split('.')
            if len(seq)==1:
                obj = self.lookup(name)
                if obj is None:
                    raise KeyError("Name '{0}' does not exist in scope".format(name))
                return obj
            else:
                return self[tuple(seq)]

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

@model
class Declaration:
    scope = ref(inv=Scope.declarations)
    def __init__(self, scope):
        self.scope = scope


@model
class Named(Declaration):
    name = attr(str, nullable=False)
    CheckedConstraint(LEGAL_IDENTIFIER)(name)

    def __init__(self, scope, name):
        if name in scope.symtab:
            raise NameError("Name '%s' already used in this scope" % name)
        super().__init__(scope)
        self.name = name


@model
class ModelFactory(Scope):
    '''
    This is a base class for creating and storing models.
    '''

    models = refs()

    base_lexer = get_lexer()

    def get_model(self, name):
        '''
        Return a model by the given name from this factory.
        '''
        model = self.lookup(name)
        if model is None:

            # May throw
            src = self.get_model_source(name)

            # insert a dummy entry into the symtab, (used to check for cycles)
            self.bind(name, 'forward')
            model = self.__compile(name, src)
            if model is None:
                raise ValueError("Validation failed")
            else:
                self.bind(name, model, force=True)
        elif model=='forward':
            raise ValueError("cyclical reference for module "+name)
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


        # Process imports
        for clause in ast:

            if clause[0] == 'import':
                model.add_import(clause[1], clause[2])
            elif clause[0]=='from':
                model.add_from(clause[1], *clause[2])
            elif clause[0]=='event':
                model.add_event(clause[1], clause[2])
            elif clause[0]=='func':
                clauses = clause[1:4]+clause[4]
                model.add_function(* clauses)
            elif clause[0] in ('fexpr', 'const'):
                name = clause[1]
                rtype = TypeInfo.forName(clause[2])
                expr = transform_expression(clause[3], model)
                constdecl = clause[0]=='const'
                model.add_fexpr(name, rtype, expr, constdecl)
            elif clause[0] == 'var':
                name = clause[1]
                vtype = TypeInfo.forName(clause[2])
                initval = transform_expression(clause[3], model)
                model.add_variable(name, vtype, initval)
            elif clause[0] == 'action':
                evtname = clause[1][1] # ('id', 'a','b') -> ('a','b')
                event = model[evtname]                
                stmt = transform_statement(clause[2], event.action_scope(model))
                model.add_action(event, stmt)


        return model

    def get_model_source(self, name):
        '''
        This method retrieves the source code of a vectorl model by name.
        It is implemented by subclasses of ModelFactory.
        '''
        raise NotImplemented

    def add_model(self, name):
        m = Model(self)
        self.bind(name, m)
        return m

    def init_system_model(self):
        sysm = self.sysmodel
        # add the Init event
        sysm.add_event('Init',[])

    def __init__(self):
        super().__init__()

        # create the system model
        self.sysmodel = None
        self.sysmodel = self.add_model('sys')
        self.init_system_model()

@model
class Model(Scope):
    '''
    A model is the result of the translation of a vectorl document
    '''

    factory = ref(inv=ModelFactory.models)
    ast = attr(list)
    imports = refs()
    importers = refs(inv=imports)
    actions=refs()

    def __init__(self, factory):
        super().__init__(factory.sysmodel)
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

    def add_from(self, modelname, *names):
        model = self.__do_import(modelname)
        for name in names:
            # note: obj should be searched in symtab, not using model.lookup
            obj = model.symtab[name]
            self.bind(name, obj)

    def add_event(self, name, params):
        e = Event(self, name, params)
        self.bind(name, e)
        return e

    def add_function(self, name, rtype, params, decl, expr):        
        e = Function(self, name, rtype, params, decl, expr)
        self.bind(name, e)
        return e

    def add_fexpr(self, name, rtype, expr, const):
        e = FExpr(self, name, rtype, expr, const)
        self.bind(name, e)
        return e

    def add_variable(self, name, type, initval):
        e = Variable(self, name, type, initval)
        self.bind(name, e)
        return e

    def add_action(self, event, stmt):
        if not isinstance(event, Event):
            raise ValueError('the first argument is not an event')
        e = Action(self, event, stmt)
        return e

    def validate(self):
        pass

    @staticmethod
    def is_type(t):
        return t in ('bool','int','real','time')


IS_TYPE = Constraint(Model.is_type, " is a type")



Parameter = namedtuple('Parameter', ['name','type'])


@model
class Function(Named):
    '''A template for creating formulas.'''
    rtype = attr(TypeInfo, nullable=False)
    params = attr(list, nullable=False)
    constdecl = attr(bool, nullable=False, default=False)
    local_scope = attr(Scope, nullable=False)


    def __init__(self, model, name, rtype, 
            params, 
            declarations, expression, 
            constdecl=False):
        super().__init__(model, name)
        self.rtype = rtype
        self.params = [Parameter(name=n, type=t) for t,n in params]
        self.declarations = declarations
        self.expression = expression
        self.constdecl = constdecl

        # Make a private scope, extending the model scope
        self.local_scope = Scope(model)

        # add params to the scope
        for p in params: self.local_scope.bind(p.name, p)

        # Check declarations for names agains the scope
        def checknames(nset):
            for name in nset:
                print("Check name ",name)
                self.local_scope[name[1:]]
        checkednames = set()
        newnames = set()
        for d in declarations:
            assert d[0] in ('const', 'fexpr')
            newnames = {n for n in collect_names(d[3])}
            checknames(newnames-names, scope)
            checkednames |= newnames
            newnames = { ('id', d[1]) }
        newnames |= set(collect_names(expression))
        checknames(newnames)

        # ok, all names are legal in scope, we can
        # succeed!

    def instantiate(self, *args):
        '''Instantiate a function call for the
        given arguments'''

        # check no. of arguments
        if len(args)!=len(self.params):
            raise ValueError("number of arguments==%d does not match parameters==%d", 
                (len(args), len(self.params)))

        # prepare arguments checking types
        cargs = [a for a in args]
        scope = Scope(self.local_scope)
        for i in range(len(args)):
            tparam = TypeInfo.forName(self.params[i].type)
            targ = args[i].type
            if not TypeInfo.auto_castable(targ, tparam):
                raise TypeError("wrong type for parameter %s, expected %s, got %s" 
                    % (self.params[i].name, tparam.name, targ.name))

            # ok bind it to the invocation scope
            carg = args[i].cast_if_needed(tparam)
            scope.bind(self.params[i].name, Argument(carg))

        # transform declarations 
        for d in self.declarations:
            expr = translate_expression(d.expression, scope)
            scope.bind(d.name, Argument(expr))

        expr = transform_expression(self.expression, scope)
        return expr


@model
class Argument:
    '''
    An argument contains a translated expression and is 
    bound to some scope
    '''
    def __init__(self, carg):
        self.arg = carg



@model
class FExpr(Named):
    '''
    An fexpr formula is an encapsulation of an expression.
    '''
    rtype = attr(TypeInfo, nullable=False)
    expr = attr(ExprNode, nullable=False)
    constdecl = attr(bool, nullable=False)

    def __init__(self, scope, name, rtype, expr, constdecl):
        super().__init__(scope, name)
        self.rtype = rtype
        self.expr = expr
        if constdecl != expr.const:
            raise ValueError("exprected a constant expression")
        self.constdecl = constdecl

@model
class Variable(Named):
    '''
    A state variable.
    '''
    type = attr(TypeInfo, nullable=False)
    initval = attr(ExprNode, nullable=False)

    @property 
    def shape(self):
        return initval.shape

    def __init__(self, scope, name, type, initval):
        super().__init__(scope, name)
        self.type = type
        self.initval = initval 

@model
class Event(Named):
    '''
    An event is emitted from event handlers, 
    or from the environment.
    '''
    params = attr(list, nullable=False)
    actions = refs()

    def __init__(self, model, name, params):
        super().__init__(model, name)
        self.params = [Parameter(name=n, type=t) for t,n in params]

    def action_scope(self, model):
        """Create a new subscope of model, to use for actions on that 
        model."""
        scope = Scope(model)
        for p in self.params:
            ptype = TypeInfo.forName(p.type)
            pival = Constant(0, ptype)
            pvar = Variable(model, p.name, ptype, pival)
            scope.bind(p.name, pvar)
        return scope


@model
class Statement:
    '''
    A statement is a basic unit of action. Each statement is in a code block or
    it is 'top-level'
    '''
    pass

@model
class Assignment(Statement):
    lhs = attr(ExprNode, nullable=False)
    rhs = attr(ExprNode, nullable=False)
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

@model
class EmitStatement(Statement):
    event = attr(Event, nullable=False)
    args = attr(list, nullable=False)
    after = attr(ExprNode, nullable=False)
    def __init__(self, event, args, after):
        self.event = event
        self.args = args
        self.after = after


@model
class IfStatement(Statement):
    condition = attr(ExprNode, nullable=False)
    then_statement = attr(Statement, nullable=False)
    else_statement = attr(Statement, nullable=True)
    def __init__(self, c, t, e=None):
        self.condition = condition
        self.then_statement = t 
        self.else_statement = e 


@model
class PrintStatement(Statement):
    args = attr(list)  # list of strings and ExprNodes
    def __init__(self, *args):
        self.args = list(args)

@model
class CodeBlock(Statement):
    '''
    A code block encapsulates a block statement.
    '''
    statements = attr(list, nullable=False)


@model
class Action:
    '''
    A template for event handlers for events of
    a particular type.
    '''
    model = ref(inv=Model.actions)
    event = ref(inv=Event.actions)
    statement = attr(Statement, nullable=False)    

    def __init__(self, model, evt, stmt):
        self.model = model
        self.event = evt
        self.statement = stmt




VECTORL_MODEL = {
    ExprNode, VarRef, Constant, Operator,

    ModelFactory, Model, Named, Scope, Declaration, Event, Action, Function, Argument,
    FExpr, Variable, Statement, CodeBlock, Assignment, IfStatement, PrintStatement,
    EmitStatement
}

import sys
assert validate_classes(VECTORL_MODEL, outfile=sys.stdout, detail=20)


#
#  AST collect expression names
#
def collect_names(* asts):
    for ast in asts:
        if ast is None: continue
        if ast[0]=='concat':
            yield from collect_names(* ast[1])
        elif ast[0]=='fcall':
            yield ast[1]
            yield from collect_names(* ast[2])
        elif ast[0]=='index':
            yield from collect_names(ast[1])
            for idx in ast[2]:
                if isinstance(idx, slice):
                    yield from collect_names(idx.start, idx.end)
                elif idx not in (..., '_'):
                    yield from collect_names(idx)
        elif ast[0] in ('cast','unary'):
            yield from collect_names(ast[2])
        elif ast[0] == 'binary':
            yield from collect_names(* ast[2:4])
        elif ast[0] == 'cond':
            yield from collect_names(* ast[1:4])
        elif ast[0] == 'id':
            yield ast



#
#  AST transformation
#

_transform_map = {}
def optype(opt):
    def declare_transform(func):
        _transform_map[opt] = func
        return func
    return declare_transform

def transform_expression(ast, scope):
    '''
    Main switch for expressions
    '''
    optype = ast[0]
    assert optype in ('literal', 'id', 'concat', 'fcall', 
        'index', 'cond', 'unary', 'binary')
    return _transform_map[optype](ast, scope)


@optype('literal')
def transform_literal(ast, scope):
    return Constant(ast[1])


@optype('id')
def transform_id(ast, scope):
    qual_id = ast[1:]
    obj = scope[qual_id] 

    # Found object, now make it into an expression, 
    # if applicable.
    if isinstance(obj, Variable):
        return VarRef(obj)
    elif isinstance(obj, FExpr):
        return obj.expr

    raise ValueError("Name '%s' is not an expression",
        '.'.join(qual_id))

@optype('concat')
def transform_concat(ast, scope):
    ast_expr_list = ast[1]
    expr_list = [transform_expression(e, scope)
        for e in ast_expr_list]
    return Operator(OPERATOR['concat'], *expr_list)

@optype('fcall')
def transform_fcall(ast, scope):
    # find Function def
    func = scope[ast[1]]
    expr_list = [transform_expression(e, scope) 
        for e in ast[2]]

    # builtin function: ignore for now
    if not isinstance(func, Function):
        raise NotImplemented

    # our function: instantiate
    return func.instantiate(*expr_list)

@optype('unary')
def transform_unary(ast, scope):
    uop = ast[1]

    expr = transform_expression(ast[2], scope)
    # + is a noop
    if uop=='+':
        return expr

    # create an operator
    opmodel = OPERATOR['unary'][uop]
    return create_operator_node(opmodel, expr)

@optype('binary')
def transform_binary(ast, scope):
    bop = ast[1]

    lhs = transform_expression(ast[2], scope)
    rhs = transform_expression(ast[3], scope)

    # create an operator
    opmodel = OPERATOR['binary'][bop]
    return create_operator_node(opmodel, lhs, rhs)


@optype('cond')
def transform_cond(ast, scope):
    sel = transform_expression(ast[1], scope)
    lhs = transform_expression(ast[2], scope)
    rhs = transform_expression(ast[3], scope)

    # create an operator
    opmodel = OPERATOR['cond']
    return create_operator_node(opmodel, sel, lhs, rhs)

@optype('index')
def transform_index(ast, scope):
    base = transform_expression(ast[1], scope)

    def transform_index_op(op):
        if op in (..., '_'):
            return op
        if isinstance(op, slice):
            start = transform_expression(op.start, scope) \
              if op.start is not None else None
            stop = transform_expression(op.stop, scope) \
              if op.stop is not None else None
            return slice(start, stop)
        # simple indexing
        return transform_expression(op, scope)

    # Now, for the strider it is a weeny bit tricky
    strider = [transform_index_op(op) for op in ast[2]]

    # Ok, now we create the opmodel
    opmodel = OPERATOR['index']

#    return create_operator_node(opmodel, base, strider)

#
#  Transform statemenst
#


def transform_statement(stmt, scope):
    optype = stmt[0]
    assert optype in ('block', 'assign', 'emit', 'print', 'if', 'fexpr', 'const')
    return _transform_map[optype](stmt, scope)




@optype('assign')
def transform_assignment(stmt, scope):
    lhs = transform_expression(stmt[1])
    rhs = transform_expression(stmt[2])

    # check lvalue
    if not lhs.lvalue:
        raise ValueError("The left-hand side of assignment is not an lvalue")

    # check compatibility
    if not lhs.bradcastable(rhs):
        raise ValueError("The right-hand side of assignment is not broadcastable to the left-hand side")

    return Assignment(lhs, rls)

@optype('if')
def transform_if(stmt, scope):
    cond = transform_expression(stmt[1],scope)
    ts = transform_statement(stmt[2], scope)
    es = transform_statement(stmt[3], scope) if stmt[3] is not None else None

    # check 
    if not cond.is_scalar():
        raise ValueError("'if' condition must be scalar")
    if cond.type != BOOL:
        raise TypeError("'if' condition must be boolean (use a cast)")

    return IfStatement(cond,ts,es)

@optype('emit')
def transform_emit(stmt, scope):
    event = scope[stmt[1][1:]]
    params = [transform_expression(p,scope) for p in stmt[2]]
    after = transform_expression(stmt[3], scope)

    # check parameters
    nep = len(event.params)
    np = len(params)
    if nep!=np:
        raise TypeError("event takes {0} parameters ({1} given)".format(nep,np))
    for i in range(nep):
        ep = event.params[i]
        p = params[i]
        if not TypeInfo.auto_castable(p.type, ep.type):
            raise TypeError("parameter {0} is {1} ({2} given)".format(ep.name, ep.type, p.type))
        if not p.is_scalar():
            raise ValueError("parameter {0} is not scalar".format(ep.name))

    # check after
    if not after.auto_castable(TIME):
        raise TypeError("Cannot cast {0} to time in 'after' clause".format(after.type))

    return EmitStatement(event, params, after)

@optype('print')
def transform_print(stmt, scope):
    params = []
    for p in stmt[1]:
        if isinstance(p, str):
            params.append(p)
        else:
            expr = translate_expression(p, scope)
            params.append(expr)

    return PrintStatement(params)

@optype('block')
def transform_block(stmt, scope):
    statements = []
    for s in stmt[1]:
        statements.append(transform_statement(s, scope))
    return CodeBlock(statements)


@optype('fexpr')
@optype('const')
def transform_fexpr(stmt, scope):
    constdecl = stmt[0]=='const'
    name = stmt[1]
    rtype = TypeInfo.forName(stmt[2])
    expr = transform_expression(stmt[3], scope)
    fexpr = FExpr(scope, name, rtype, expr, constdecl)
    scope.bind(name, fexpr)
    return fexpr

    


#
# Parser
#

# error handling 
def comperr(p, line, msg, *args, **kwargs):
    lexerr(p.lexer, line, msg, *args, **kwargs)

def lexerr(lex, line, msg, *args, **kwargs):
    name = lex.modelname
    errmsg = msg.format(*args, **kwargs)
    print("error:", "{0}({1}): {2}".format(name, line, errmsg))



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
    "func_decl : DEF typename ID LPAREN arglist RPAREN body "
    p[0] = ('func', p[3], p[2], p[5], p[7], p.lineno(1) )


def p_body(p):
    "body : LBRACE declarations expression RBRACE "
    p[0] = (p[2], p[3])


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
    """ fexpr_decl : DEF typename ID EQUALS expression SEMI """
    p[0] = ('fexpr', p[3],p[2],p[5])

def p_cexpr_decl(p):
    """ fexpr_decl : CONST typename ID EQUALS expression SEMI """
    p[0] = ('const', p[3],p[2],p[5])

# variables

def p_var_decl(p):
    """ var_decl : VAR typename ID EQUALS expression SEMI """
    p[0] = ('var', p[3], p[2], p[5])

# actions

def p_event_action(p):
    """ action_decl : ON qual_id statement """
    p[0] = ('action', p[2], p[3])

#
# statements (allowed in actions)
#

def p_block_statement(p):
    """ statement : LBRACE statements RBRACE """
    p[0] = ('block', p[2])

def p_statements_opt(p):
    " statements : "
    p[0] = []

def p_statements(p):
    "statements : statements statement"
    p[0] = p[1] + [p[2]]

def p_emit_statement(p):
    " statement : EMIT qual_id LPAREN expr_list_opt RPAREN AFTER expression SEMI "
    p[0] = ('emit', p[2],p[4],p[7])

def p_assignment(p):
    " statement : expression ASSIGN expression SEMI "
    p[0] = ('assign', p[1], p[3])

def p_fexpr_statement(p):
    " statement : fexpr_decl "
    p[0] = p[1]


#  PRINT


def p_print_statement(p):
    " statement : PRINT LPAREN print_args_opt RPAREN SEMI"
    p[0] = ('print', p[3])

def p_print_args_none(p):
    " print_args_opt : "
    p[0] = []
def p_print_args_some(p):
    " print_args_opt : print_args "
    p[0] = p[1]
def p_print_args_one(p):
    " print_args : print_arg " 
    p[0] = [p[1]]
def p_print_args_many(p):
    " print_args : print_args COMMA print_arg "
    p[0] = p[1] + [p[3]]
def p_print_arg(p):
    """ print_arg : STRCONST 
                  | expression """
    p[0] = p[1]

# IF

def p_if_statement(p):
    """ statement : IF LPAREN expression RPAREN statement 
                  | IF LPAREN expression RPAREN statement ELSE statement
    """
    assert len(p) in (6,8)
    if len(p)==6:
        p[0] = ('if', p[3], p[5], None)
    else:
        p[0] = ('if', p[3], p[5], p[7])


#
# Expression grammar
#

def p_primary_expression_literal_int(p):
    " primary_expression : ICONST "
    p[0] = ('literal', int(p[1]))

def p_primary_expression_literal_float(p):
    " primary_expression : FCONST "
    p[0] = ('literal', float(p[1]))

def p_primary_expression_literal_bool(p):
    """ primary_expression : TRUE 
                           | FALSE  """
    p[0] = ('literal', p[1]=='true') 

def p_primary_expression_id(p):
    """ primary_expression :  qual_id """
    p[0] = p[1]

def p_qual_id(p):
    """ qual_id : ID 
                | ID PERIOD qual_id"""
    if len(p)==4:
        p[0] =  ('id', p[1]) + p[3][1:]
    else:
        p[0] = ('id', p[1])

def p_primary_expression_paren(p):
    """ primary_expression :  LPAREN expression RPAREN  """
    p[0] =  p[2]

def p_primary_expression_concat(p):
    """ primary_expression : LBRACKET expr_list RBRACKET """
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
            p[0] = (...,)
        else:
            p[0] = p[1]
    else:
        if p[1]=='ELLIPSIS':
            p[0] = (...,)+p[3]
        else:
            p[0] = p[1]+(...,)


def p_index_seq(p):
    """ index_seq : index_op 
                  | index_seq COMMA index_op """
    if len(p)==2:
        p[0] = (p[1],)
    else:
        p[0] = p[1]+(p[3],)

def p_index_op_index(p):
    " index_op : expression "
    p[0]=p[1]

def p_index_op_range(p):
    " index_op : expr_opt COLON expr_opt"
    p[0] = slice(p[1],p[3])

def p_index_op_newdim(p):
    " index_op : SUB "
    p[0] = '_'


def p_expr_opt(p):
    """ expr_opt : 
                 | expression """
    assert len(p) in (1,2)
    if len(p)==1:
        p[0] = None
    else:
        p[0] = p[1]

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
                | NOT
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

def p_land_expression(p):
    """ land_expression : or_expression 
                    | land_expression LAND or_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])

def p_lor_expression(p):
    """ lor_expression : land_expression 
                    | lor_expression LOR land_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])


def p_expression(p):
    """ expression : lor_expression 
                    | lor_expression CONDOP expression COLON expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('cond', p[1], p[3], p[5])




parser = yacc.yacc()


