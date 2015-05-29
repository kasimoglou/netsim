

from models.mf import *
from models.constraints import is_legal_identifier, LEGAL_IDENTIFIER

from vectorl.base import AstNode, SourceItem, AstContext
from vectorl.lexer import tokens, get_lexer
from vectorl.parser import parser
from vectorl.expr import *
from vectorl.builtins import builtins, sys_builtins, Builtin

from functools import wraps

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

    def __init__(self, superscope=None, init={}):
        self.symtab = dict(init)
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
                    print("scope = ",self.symtab)
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
class Named(SourceItem):
    scope = ref(inv=Scope.declarations)
    name = attr(str, nullable=False)
    CheckedConstraint(LEGAL_IDENTIFIER)(name)

    def __init__(self, scope, name):
        if name in scope.symtab:
            raise NameError("Name '%s' already used in this scope" % name)
        self.scope = scope
        self.name = name


@model
class ModelFactory(Scope):
    '''
    This is a base class for creating and storing models.
    '''

    models = refs()
    model_order = attr(list)

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
                self.add_model(model, force=True)
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
        '''
        Parse src into the ast for a new model.
        '''
        # Create a new lexer
        lexer = self.base_lexer.clone()
        lexer.factory = self
        lexer.modelname = name

        # parse
        ast = parser.parse(src, lexer=lexer, tracking=True)
        return ast


    def __transform(self, name, ast):
        '''
        Return a new model with the given name, initialized by the given 
        ast.
        '''
        model = Model(self, name)
        model.ast = ast

        transform_model(ast, model)

        return model

    def get_model_source(self, name):
        '''
        This method retrieves the source code of a vectorl model by name.
        It is implemented by subclasses of ModelFactory.
        '''
        raise NotImplementedError("get_model_source() must be implemented in a subclass")

    def add_model(self, model, force=False):
        self.bind(model.name, model, force=force)
        self.model_order.append(model)
        return model

    def init_system_model(self):
        # add the Init event
        sysm = Model(self, 'sys')
        sysm.add_event('Init',[])
        for name, func in sys_builtins.items():
            sysm.bind(name, func)
        return sysm


    def all_events(self):
        '''
        Return all event declarations in all modules.
        '''
        for model in self.model_order:
            for event in model.events:
                yield event

    def all_variables(self):
        '''
        Return all variables in all modules. Variables are returned
        in dependency order (dependents come later).
        '''
        for model in self.model_order:
            for var in model.variables:
                yield var

    def __init__(self):
        super().__init__()

        # create the system model
        self.model_order = []
        self.sysmodel = None  # this is NEEDED, because of a recursive access!
        self.sysmodel = self.init_system_model()
        self.add_model(self.sysmodel)




@model
class Model(Scope):
    '''
    A model is the result of the translation of a vectorl document
    '''

    factory = ref(inv=ModelFactory.models)
    name = attr(str, nullable=False)
    ast = attr(list)
    imports = refs()
    importers = refs(inv=imports)
    actions=ref_list()
    events=refs()
    variables=ref_list()

    def __init__(self, factory, name):
        super().__init__(factory.sysmodel, init=builtins)
        self.factory = factory
        self.name = name

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


#
#  Other entities
#


IS_TYPE = Constraint(Model.is_type, " is a type")


@model
class Function(Named):
    '''A template for creating formulas.'''
    rtype = attr(TypeInfo, nullable=False)
    params = attr(list, nullable=False)
    constdecl = attr(bool, nullable=False, default=False)
    expression = attr(ExprNode, nullable=False)

    def __init__(self, model, name, rtype, 
            params, declarations, expression):
        super().__init__(model, name)
        self.rtype = rtype
        self.params = params
        self.declarations = declarations
        self.expression = expression

    def instantiate(self, *args):
        '''Instantiate a function call for the
        given arguments'''

        # check no. of arguments
        if len(args)!=len(self.params):
            raise ValueError("no. of arguments==%d does not match no. of parameters==%d", 
                (len(args), len(self.params)))

        argmap = {}

        for param,arg in zip(self.params, args):
            if not arg.type.auto_castable(param.type):
                raise TypeError("wrong type for parameter %s, expected %s, got %s" 
                    % (param.name, param.type.name, arg.type.name))
            argmap[param.name] = arg

        return self.expression.bind(argmap)



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
        if constdecl > expr.const:
            raise ValueError("exprected a constant expression")
        self.constdecl = constdecl

@model
class Variable(Named):
    '''
    A state variable.
    '''
    type = attr(TypeInfo, nullable=False)
    initval = attr(ExprNode, nullable=False)
    model = ref(inv=Model.variables)

    @property 
    def shape(self):
        return initval.shape

    def __init__(self, scope, name, type, initval):
        super().__init__(scope, name)
        self.type = type
        self.initval = initval

        # Find the model you belong to
        self.model = scope

    @property
    def full_name(self):
        return "%s.%s" % (self.model.name, self.name)

@model
class Event(Named):
    '''
    An event is emitted from event handlers, 
    or from the environment.
    '''
    params = attr(list, nullable=False)

    # variables used to hold parameter values during
    # action calls
    variables = attr(list, nullable=False)

    actions = ref_list()
    model = ref(inv=Model.events)

    def __init__(self, model, name, params):
        super().__init__(model, name)
        self.params = params
        self.model = model
        self.variables = []
        for param in self.params:
            pvar = Variable(model, param.name, param.type, Literal(0, param.type))
            self.variables.append(pvar)

    def action_scope(self, model):
        """Create a new subscope of model, to use for actions on that 
        model."""
        scope = Scope(model)
        for p in self.variables:
            scope.bind(p.name, p)
        return scope

    def __repr__(self):
        return "Event(%s.%s)" % (self.model.name, self.name)

@model
class Statement(SourceItem):
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
        self.condition = c
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

    def __init__(self, stmts):
        self.statements = stmts

@model
class Action(SourceItem):
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
    SourceItem,
    ExprNode, VarRef, Literal, Operator, Parameter, 

    ModelFactory, Model, Named, Scope, Event, Action, Function, 
    FExpr, Variable, Statement, CodeBlock, Assignment, IfStatement, PrintStatement,
    EmitStatement
}



#
#  AST transformation
#

_transform_map = {}
def optype(*opt):
    def declare_transform(func):
        @wraps(func)
        def ast_advice(ast, scope):
            if isinstance(ast, AstNode):
                with AstContext(ast):
                    retval = func(ast, scope)
                    if isinstance(retval, SourceItem):
                        retval.ast = ast
            else:
                retval = func(ast, scope)                
            return retval
        for o in opt:
            _transform_map[o] = ast_advice
        return ast_advice
    return declare_transform

def transform_expression(ast, scope):
    '''
    Main switch for expressions
    '''
    optype = ast[0]
    assert optype in ('literal', 'array', 'id', 'concat', 'fcall', 
        'index', 'cond', 'unary', 'binary')
    return _transform_map[optype](ast, scope)


@optype('literal')
def transform_literal(ast, scope):
    return Literal(ast[1])


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
    elif isinstance(obj, Parameter):
        return obj

    raise ValueError("Name '%s' is not an expression",
        '.'.join(qual_id))

@optype('concat')
def transform_concat(ast, scope):
    ast_expr_list = ast[1]
    expr_list = [transform_expression(e, scope)
        for e in ast_expr_list]
    return Concat(*expr_list)

@optype('array')
def transform_concat(ast, scope):
    ast_expr_list = ast[1]
    expr_list = [transform_expression(e, scope)
        for e in ast_expr_list]
    return Array(*expr_list)


@optype('fcall')
def transform_fcall(ast, scope):
    # find Function def
    assert ast[1][0]=='id'
    func = scope[ast[1][1:]]

    expr_list = [transform_expression(e, scope) 
        for e in ast[2]]

    # builtin function: ignore for now
    if isinstance(func, type) and issubclass(func, Builtin):
        return func(* expr_list)

    if isinstance(func, Function):
        return func.instantiate(*expr_list)

    assert False

@optype('unary')
def transform_unary(ast, scope):
    uop = ast[1]

    expr = transform_expression(ast[2], scope)
    # + is a noop
    if uop=='+':
        return expr

    # create an operator
    if uop=='-': return -expr
    if uop=='~': return ~expr
    if uop=='!': return LNOT(expr)
    assert False

@optype('binary')
def transform_binary(ast, scope):
    bop = ast[1]

    lhs = transform_expression(ast[2], scope)
    rhs = transform_expression(ast[3], scope)

    # create an operator
    if bop=='+': return lhs + rhs
    if bop=='-': return lhs - rhs
    if bop=='*': return lhs * rhs
    if bop=='/': return lhs / rhs
    if bop=='%': return lhs % rhs

    if bop=='<<': return lhs << rhs
    if bop=='>>': return lhs >> rhs
    
    if bop=='&': return lhs & rhs
    if bop=='|': return lhs | rhs
    if bop=='^': return lhs ^ rhs

    if bop=='==': return lhs == rhs
    if bop=='!=': return lhs != rhs
    if bop=='<': return lhs < rhs
    if bop=='<=': return lhs <= rhs
    if bop=='>': return lhs > rhs
    if bop=='>=': return lhs >= rhs


@optype('cond')
def transform_cond(ast, scope):
    sel = transform_expression(ast[1], scope)
    lhs = transform_expression(ast[2], scope)
    rhs = transform_expression(ast[3], scope)

    # create an operator
    return IF(sel, lhs, rhs)

@optype('index')
def transform_index(ast, scope):
    base = transform_expression(ast[1], scope)

    def transform_index_op(op):
        if op is ...: return op
        if op=='_': return None
        if isinstance(op, slice):
            start = transform_expression(op.start, scope) \
              if op.start is not None else None
            stop = transform_expression(op.stop, scope) \
              if op.stop is not None else None
            return slice(start, stop)
        # simple indexing
        return transform_expression(op, scope)

    # Now, for the strider it is a weeny bit tricky
    indexer = tuple([transform_index_op(op) for op in ast[2]])

    return base[indexer]


#
#  Transform statements
#


def transform_statement(stmt, scope):
    optype = stmt[0]
    assert optype in ('block', 'assign', 'emit', 'print', 'if', 'fexpr', 'const')
    return _transform_map[optype](stmt, scope)




@optype('assign')
def transform_assignment(stmt, scope):
    lhs = transform_expression(stmt[1], scope)
    rhs = transform_expression(stmt[2], scope)

    # check lvalue
    if not lhs.lvalue:
        raise ValueError("The left-hand side of assignment is not an lvalue")

    # check compatibility
    if not lhs.broadcastable(rhs):
        raise ValueError("The right-hand side of assignment is not broadcastable to the left-hand side")

    return Assignment(lhs, rhs)

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
        if not p.type.auto_castable(ep.type):
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
            expr = transform_expression(p, scope)
            params.append(expr)

    return PrintStatement(* params)

@optype('block')
def transform_block(stmt, scope):
    statements = []
    for s in stmt[1]:
        statements.append(transform_statement(s, scope))
    return CodeBlock(statements)


@optype('fexpr','const')
def transform_fexpr(stmt, scope):
    constdecl = stmt[0]=='const'
    name = stmt[1]
    rtype = TypeInfo.forName(stmt[2])
    expr = transform_expression(stmt[3], scope)
    fexpr = FExpr(scope, name, rtype, expr, constdecl)
    scope.bind(name, fexpr)
    return fexpr


#
#  Main model
#

def transform_params(plist, scope, shape=None):
    params = []
    for t,n in plist:
        p = Parameter(name=n, type=TypeInfo.forName(t), shape=shape)
        scope.bind(n, p)
        params.append(p)
    return params

@optype('import')
def transform_import(clause, model):
    assert isinstance(model, Model)
    assert clause[0]=='import'

    model.add_import(clause[1], clause[2])

@optype('from')
def transform_import(clause, model):
    assert isinstance(model, Model)
    assert clause[0]=='from'

    model.add_from(clause[1], *clause[2])


@optype('event')
def transform_event(clause, model):
    params = [Parameter(name=n,type=TypeInfo.forName(t), 
        shape=tuple()) for t,n in clause[2]]
    return model.add_event(clause[1], params)


@optype('var')
def transform_var(clause, model):
    name = clause[1]
    vtype = TypeInfo.forName(clause[2])
    initval = transform_expression(clause[3], model)
    return model.add_variable(name, vtype, initval)


@optype('action')
def transform_action(clause, model):
    evtname = clause[1][1:] # ('id', 'a','b') -> ('a','b')
    event = model[evtname]                
    assert isinstance(event, Event), "%s does not name an event" % evtname
    stmt = transform_statement(clause[2], event.action_scope(model))
    return model.add_action(event, stmt)


@optype('func')
def transform_function(clause, scope):
    name = clause[1]
    rtype = TypeInfo.forName(clause[2])
    fscope = Scope(scope)
    args = transform_params(clause[3], fscope)

    astdecl, astexpr = clause[4]

    decls = [transform_fexpr(d, fscope) for d in astdecl]
    expr = transform_expression(astexpr, fscope)

    func = Function(scope, name, rtype, args, decls, expr)
    scope.bind(name, func)
    return func


def transform_model(ast, model):

    # Process imports
    for clause in ast:
        assert clause[0] in ('import', 'from', 'event', 'func',
            'fexpr', 'const', 'var', 'action')
        optype = clause[0]
        _transform_map[optype](clause, model)

    return model
