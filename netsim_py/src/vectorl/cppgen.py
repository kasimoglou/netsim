
from vectorl.typeinfo import *
from vectorl.expr import *
from vectorl.model import *
from models.mf import *

from simgen.utils import docstring_template

import io
from functools import wraps
from contextlib import contextmanager

def emit_indented(m, values):
    'return a string with the contents of value indented by m tabs'
    with io.StringIO() as out:
        indent = '\t'*m
        for v in values:
            with io.StringIO(v) as f:
                for line in f.readlines():
                    out.write(indent)
                    out.write(line)
        return out.getvalue()

def emit_indented_blocks(values, m='', out=None):
    """Return a string for the recursive list 'values'.
    This list contains both strings and other lists.
    The contents are indented according the the nesting
    level, and returned as a single text.
    """
    if out is None: 
        out = io.StringIO()
        print('values=',values)


    for v in values:
        if isinstance(v, list):
            out.write(m+"{\n")
            emit_indented_blocks(v, m+'\t', out)
            out.write(m+"}\n")
        else:
            assert isinstance(v, str)
            out.write(m)
            out.write(v)
            out.write('\n')
    return out.getvalue()




def shape_size(shape):
    "Return the total number of elements of an array or scalar"
    prod = 1
    for i in shape:
        prod *= i
    return prod


cppgen_map = {}

def gen_item(item):
    "Decorator for switching on generation methods"
    def map_method(method):
        cppgen_map[item] = method
        return method
    return map_method


@contextmanager
def nested_code(gen):
    gen.push_code()
    yield
    gen.pop_code()


class CppGenerator:
    def __init__(self, factory, class_name):
        self.factory = factory
        self.output_cc = None
        self.output_hh = None
        self.class_name = class_name

        self.code_stack = []
        self.code = []

        self.const_decl = []

        self.name_counter = 0


    def getname(self, prefix):
        self.name_counter += 1
        return "_%s%d" % (prefix, self.name_counter)


    def push_code(self):
        self.code_stack.append(self.code)
        self.code = list()

    def pop_code(self):
        curcode = self.code
        self.code = self.code_stack.pop()
        self.code.append(curcode)


    def generate(self):
        'This is the main function to perform the generation'
        self.generate_vars()
        self.generate_actions()
        self.generate_class_decl()
        self.generate_class_def()


    def generate_class_decl(self):
        pieces = list(self.struct_src.values()) + list(self.action_decl.values())
        self.output_hh = self.class_decl(pieces)

    @docstring_template
    def class_decl(self, allval):
        """\
//------------------------------------------------
// Automatically generated by the vectorl compiler
// (changes will be overwritten)
//-------------------------------------------------
#ifndef {{!cpp_label}}
#define {{!cpp_label}}

#include <boost/multi_array.hh>

struct {{self.class_name}} {
    
{{! body}}

};


#endif

"""
        cpp_label = self.class_name.upper()+"_HH"
        body = emit_indented(1, allval)
        return locals()


    def generate_class_def(self):
        action_text = []
        for event in self.action_def:
            atext = self.gen_action_def(event)
            action_text.append(atext)
        self.output_cc = self.gen_cc_file(action_text)


    @docstring_template
    def gen_cc_file(self, action_text):
        """
#include "{{!self.class_name}}"

{{! actions}}
"""
        actions = "".join(action_text)      
        return locals()

    @docstring_template
    def gen_action_def(self, event):
        """\
{{! header}}
{{! body}}

"""
        adef = self.action_def[event]
        # generate method header
        header = self.gen_action_def_header(event)

        # generate method body
        body = emit_indented_blocks(adef)
        return locals()


    @docstring_template
    def gen_action_def_header(self, event):
        "void {{!self.class_name}}::{{!mangled_name}}({{! param_list}})"
        mangled_name = self.mangled(event.model.name,event.name)
        param_list = self.gen_params_decl(event.variables)
        return locals()


    #------------------------------------------------------
    #
    # The variables
    #
    #------------------------------------------------------

    def generate_vars(self):
        self.var_map = {}
        self.struct_src = {}

        for model in self.factory.models:
            self.struct_src[model.name] = self.generate_struct(model)


    def is_model_level(self, var):
        '''Return true iff a var is declared at the model level'''
        return var.name in var.model and var.model[var.name] is var


    @docstring_template
    def generate_struct(self, model):
        '''
struct _model_{{!model.name}} {

    // model-level variables
    % for var in model.variables:
    % if self.is_model_level(var):
    %  self.var_map[var] = "%s.%s" % (model.name, var.name)
    {{!self.gen_var_decl(var.type, var.shape, var.name)}};
    % end
    % end

} {{!model.name}};

'''
        return locals()

    def gen_type(self, tinfo):
        return self.typemap[tinfo]

    typemap = {
        BOOL: 'bool',
        INT: 'int',
        REAL: 'double',
        TIME: 'double'
    }


    @docstring_template
    def gen_var_decl(self, tinfo, shape, name):
        "{{!tname}} {{!name}}{{!extents}}"
        tname = self.gen_type(tinfo)
        extents = "".join("[%d]" % e  for e in shape)
        return locals()

    #----------------------------------------------------
    #
    # Actions (statements)
    #
    #----------------------------------------------------


    def generate_actions(self):
        self.action_decl = {}
        self.action_def = {}

        for event in self.factory.all_events():
            self.action_def[event] = self.generate_action(event)



    def generate_action(self, event):
        self.action_decl[event] = self.gen_action_decl(event)
        # mark cpp names of action params
        for var in event.variables:
            self.var_map[var] = var.name

        for action in event.actions:
            stmt = self.generate_statement(action.statement)

        # get code from the stack
        assert not self.code_stack 
        action_def = self.code
        self.code = []

        return action_def

    def mangled(self, *args):
        largs = ["%d%s"%(len(s),s) for s in args]
        return '_'.join(largs)

    @docstring_template
    def gen_action_decl(self, event):
        """void on_{{!m_event}}({{!param_list}});
"""
        m_event = self.mangled(event.model.name, event.name)
        param_list = self.gen_params_decl(event.variables)
        return locals()

    def gen_params_decl(self, vars):
        return ', '.join(self.gen_param_decl(v) for v in vars)

    @docstring_template
    def gen_param_decl(self, var):
        "{{!type}} {{!name}}"
        type = self.gen_type(var.type)
        name = var.name
        return locals()


    def generate_statement(self, stmt):
        method = cppgen_map[stmt.__class__]
        with nested_code(self):
            return method(self, stmt)


    @gen_item(Assignment)
    def generate_assign(self, stmt):

        rhs_expr = self.materialize_expression(stmt.rhs)
        self.code.append(rhs_expr.code)
        return

        lhs_var, lhs_code = self.generate_lvalue(stmt.lhs)

        lshape = stmt.lhs.shape
        rshape = stmt.rhs.shape

        if shape_size(lshape)==1:
            # we do not loop
            assert shape_size(rshape)==1
            assert len(lshape)>=len(rshape)
            code = ""
        else:
            pass
            # iteration: take all axes whose size is > 1

        return locals()


    def gen_assignment_size1(self, lhs_var, lshape, rhs_var, rshape):
        LHS = lhs_var + "[0]"*len(lshape)
        RHS = rhs_var + "[0]"*len(rshape)



    @gen_item(CodeBlock)
    def generate_code_block(self, stmt):
        stmts = []
        for stmt in stmt.statements:
            stmts.append(self.generate_statement(stmt))
        stmt=emit_indented(1, stmts)
        return locals()     

    @gen_item(EmitStatement)
    def generate_emit(self, stmt):
        pass

    @gen_item(PrintStatement)
    def generate_print(self, stmt):
        pass

    @gen_item(IfStatement)
    def generate_if(self, stmt):
        pass

    @gen_item(FExpr)
    def generate_fexpr(self, stmt):
        pass

    #-----------------------------------------------
    #
    # r-values (expressions)
    #
    #-----------------------------------------------

    def generate_expression(self, expr):
        'This is a top-level entry point to create the expression context.'
        ctx = ExprContext(self, expr)
        ret = self.generate_rvalue(ctx)
        return ctx

    def materialize_expression(self, expr):
        'This is a top-level entry point to create the expression context.'
        ctx = ExprContext(self, expr)
        return self.materialize(ctx)


    def materialize(self, ctx):
        '''
        This is a pseudo-operator which materializes the result of an
        expression to a variable.
        '''
        expr = ctx.expr

        # declare the result
        result_name = self.getname('tmp')
        code = self.gen_var_decl(expr.type, expr.shape, result_name)
        self.code.append(code + ';')

        # body of the implementation
        with nested_code(self):
            mat = ctx.materialize()
            self.generate_rvalue(ctx)

            # loop 
            mat.iterctx.gen_loops()

            # create copy expression
            lhs = mat.indexing.gen_index(result_name, expr.shape)
            rhs = ctx.code
            with nested_code(self):
                code = "%s = %s;" % (lhs, rhs)
                self.code.append(code)

        if mat.parent is None:
            mat.set_inline(result_name, VAR_PRIORITY)
        else:
            code = mat.parent.indexing.gen_index(result_name, expr.shape)
            mat.set_inline(code, VAR_PRIORITY)

        return mat

    def generate_rvalue(self, ctx):
        # Here, we first check to see if we are at a constant
        # node. This case is trated generically here, regardless of
        # node type.
        if ctx.expr.const:
            self.generate_constant(ctx)
        else:
            # dispatch to the right function
            method = cppgen_map[ctx.expr.__class__]
            return method(self, ctx)


    @gen_item(VarRef)
    def generate_var(self, ctx):
        '''
        Variables are named, return inline code
        '''
        varname = self.var_map[ctx.expr.var]
        varshape = ctx.expr.shape
        code = ctx.indexing.gen_index(varname, varshape)
        ctx.set_inline(code, VAR_PRIORITY)


    @gen_item(Literal)
    def generate_literal(self, ctx):
        '''
        Literals are always returned inline and they are not
        iterable :-)
        '''
        ctx.set_inline(self.generate_literal_value(expr.type, expr.value), 
            VAR_PRIORITY)


    def generate_literal_value(self, etype, evalue):
        '''
        Generate a C++ literal from value and type.
        '''
        if etype is BOOL:
            return "true" if evalue else "false"
        elif etype is INT or etype is REAL:
            return str(evalue)
        elif etype is TIME:
            # what?
            return self.time_literal(evalue)


    def time_literal(self, val): 
        '''
        Return the C++ representation of a time literal.
        This method may be overloaded in platform-specific subclasses.
        '''
        return str(val)


    def generate_constant(self, ctx):
        # Note that, although this context has not been visited before,
        # the expression may have been revisited
        # (because the expr tree is actually a DAG, due to
        # fexpr). In this case, we do not re-emit the constant.

        expr = ctx.expr

        if hasattr(expr, 'cpp_const'):
            # return the expression previously computed
            code = ctx.indexing.gen_index(cpp_const, ctx.shape)
            ctx.set_inline(code, VAR_PRIORITY)
            return

        # First visit!

        # A constant is returned inline if it is scalar, or
        # by name it it is array.
        if expr.is_scalar():
            # inline scalars
            expr.cpp_const = self.generate_literal_value(expr.type, expr.value)
            ctx.set_inline(expr.cpp_const, VAR_PRIORITY)
            return

        # ok, non-scalar
        # We create a const array for the value.
        assert expr.shape == expr.value.shape

        # get a name for the constant
        name = self.getname('const')
        code = self.gen_const_decl(expr.type, expr.shape, name, expr.value)

        self.const_decl.append(code)
        expr.cpp_const = name
        
        code = ctx.indexing.gen_index(name, expr.shape)
        ctx.set_inline(code, VAR_PRIORITY)

    @docstring_template
    def gen_const_decl(self, vtype, shape, name, value):
        "static const {{! vardecl}} = {{! valinit}};"
        vardecl = self.gen_var_decl(vtype, shape, name)
        valinit = self.gen_array_literal(vtype, value)
        return locals()

    def gen_array_literal(self, type, value):
        if value.ndim>1:
            res = ",\n".join(self.gen_array_literal(a) for a in value)
            return "{ "+res+ "}"
        else:
            assert value.ndim==1
            res = ", ".join(self.generate_literal_value(type, value))
            return "{ " +res+" }"


    @gen_item(UFuncOperator)
    def generate_ufunc_operator(self, ctx):
        # a non const node
        """
        When the translation reaches an operator, it does the following:
        (a) if the operator is scalar, 
            1. propagate to the operands,
            2. compose the inline expression

        (b) For non-scalar operators:

            If there is an iteration context in the parent context, 
            1. copy it
            2. propagate to the children
            3. compose the inline expression

            else
            1. create your own context,
            2. propagate to the children,
            3. compose the loop expression and close the context
            4. return inline the context variable


        """
        assert not ctx.expr.const

        if ctx.expr.is_scalar():
            self.propagate_to_contexts(ctx.argctx)
            self.compose_ufunc_expression(ctx)
        else:
            assert ctx.parent is not None
            parent = ctx.parent            
            self.propagate_to_contexts(ctx.argctx)
            self.compose_ufunc_expression(ctx)

            


    def propagate_to_contexts(self, argctx):
        for argc in argctx:
            self.generate_rvalue(argc)


    def compose_ufunc_expression(self, ctx):
        if ctx.expr.arity==1:
            self.compose_unary_ufunc_expr(ctx)
        else:
            assert ctx.expr.arity==2
            self.compose_binary_ufunc_expr(ctx)

    def compose_unary_ufunc_expr(self, ctx):
        expr = ctx.expr
        argc = ctx.argctx[0]

        # do we need parentheses?
        priority = UNARY_PRIORITY

        if argc.priority > priority:
            # inline, they are all prefix operators!
            ctx.set_inline("%s%s" % (expr.op, argc.code), priority)
        else:
            ctx.set_inline("%s(%s)" % (expr.op, argc.code), priority)
    
    def compose_binary_ufunc_expr(self, ctx):
        expr = ctx.expr
        argc = (ctx.argctx[0], ctx.argctx[1])

        # do we need parentheses?
        op = expr.op
        priority = binary_op_priority[op]

        # take care of precedence AND assosiativity (always left-assoc) in one scoop
        code0 = argc[0].code if argc[0].priority >= priority else "(%s)"%argc[0].code
        code1 = argc[1].code if argc[0].priority > priority else "(%s)"%argc[0].code

        ctx.set_inline("%s%s%s" % (code0,op,code1), priority)




    #-----------------------------------------------
    #
    # l-values
    #
    #-----------------------------------------------
    def generate_lvalue(expr, name):
        return ("", "")



@model
class IterVar:
    context = ref()
    name = attr(str)
    extent = attr(int)
    def __init__(self, context, name, extent):
        self.context = context
        self.name = name
        self.extent = extent


@model
class Index:
    context = ref()
    var = attr(IterVar, nullable=True)
    stride = attr(int, nullable=False,default=1)
    offset = attr(type=(int, str), nullable=False, default=0)

    def __init__(self, var, stride, offset):
        self.var = var
        self.stride = stride
        self.offset=offset

    def gen_code(self):
        if self.var is None or self.stride==0:
            return str(self.offset)

        vname = self.var.name
        if self.stride==1:
            cvar = vname
        elif self.stride==-1:
            cvar = '-'+vname
        else:
            cvar = "(%s)*%s" %(self.stride, vname)

        if self.offset==0:
            return "["+cvar+"]"
        else:
            return "[%s+(%s)]" % (cvar, self.offset)


@model
class IndexingContext:
    indices = ref_list(inv=Index.context)

    def gen_index(self, code, shape):
        codes = [code]
        skip = len(self.indices) - len(shape)
        for i in self.indices[skip:]:
            codes.append(i.gen_code())
        return ''.join(codes)


@model
class IterationContext:
    # the owning expression context
    context = ref()

    @property 
    def generator(self):
        return self.context.generator

    # the shape
    shape = attr(type=(list,tuple), nullable=False)

    # the variables
    iteration = ref_list(inv=IterVar.context)

    def __init__(self, context, shape):
        self.context = context
        self.shape = shape
        for s in shape:
            IterVar(self, self.context.generator.getname('i'), s)

    def gen_loops(self):
        code = self.generator.code
        for iter in self.iteration:
            code.append(self.loop(iter))

    @docstring_template
    def loop(self, iter):
        """for(int {{!i}}=0; {{!i}}!={{!n}}; ++{{!i}})"""
        i=iter.name
        n=iter.extent
        return locals()

    def indexing_context(self):
        idxc = IndexingContext()
        for ivar in self.iteration:
            idxc.indices.append(Index(ivar, 1, 0))
        return idxc



@model
class ExprContext:
    # the expression node in the model
    generator = attr(CppGenerator, nullable=False)
    expr = attr(ExprNode)

    @property 
    def shape(self):
        return self.expr.shape

    # priority (to minimize parentheses), only meaningful if inline is true
    # If inline is false, it is set to VAR_PRIORITY

    # the result
    code = attr(str, nullable=False)
    priority = attr(int, nullable=False)

    # implement the tree of operators
    argctx = ref_list()
    parent = ref(inv=argctx)

    # iteration context
    iterctx = ref(inv=IterationContext.context)

    # indexing context
    indexctx = attr(IndexingContext, nullable=True, default=None)

    def __init__(self, generator, expr):
        self.generator = generator
        self.expr = expr
        if isinstance(expr, Operator) and not expr.const:
            # populate the tree recursively
            for arg in expr.args:
                self.argctx.append(ExprContext(generator, arg))

    def set_inline(self, code, priority):
        print("setting code to",code)
        self.code = code
        self.inline = True
        self.priority = priority


    def create_iter(self, shape):
        ictx = IterationContext(self, shape)
        assert self.iterctx is ictx
        self.indexctx = ictx.indexing_context()
        assert self.indexing is not None


    @property 
    def indexing(self):
        if self.indexctx is not None: return self.indexctx
        if self.parent is not None: return self.parent.indexing
        return None


    def parent_order(self):
        if self.parent is not None:
            for i in len(self.parent.argctx):
                if self.parent.argctx[i] is self:
                    return i
            assert False,"This is an error in the mf system!"
        return None

    def materialize(self):
        '''
        Return a new context, for the same expression, and replace
        thyself both in the parent and in the children.
        '''
        matnode = ExprContext(self.generator, None)
        matnode.expr = self.expr
        # find your order
        order = self.parent_order()
        if order is not None:
            self.parent.argctx[order] = matnode
        self.parent = matnode

        # create materialized iteration
        matnode.create_iter(self.expr.shape)
        assert matnode.indexctx is not None
        assert self.indexctx is None

        assert self.indexing is matnode.indexing, "the two:{0}, {1}".format(self.indexing, matnode.indexing)

        return matnode




VAR_PRIORITY=130    # For variables, literals, constants and materialized
                   # contexts. In general, anything with a 'name'


UNARY_PRIORITY = 120
CAST_PRIORITY = 110
MULT_PRIORITY = 100
ADD_PRIORITY = 90
SHIFT_PRIORITY = 80
REL_PRIORITY = 70
EQ_PRIORITY = 65
AND_PRIORITY = 60
XOR_PRIORITY = 50
OR_PRIORITY = 40
LAND_PRIORITY = 30
LOR_PRIORITY = 20

CONCAT_PRIORITY = 10


binary_op_priority = {
    # The C++ priorities of expressions

    '*' : MULT_PRIORITY,
    '/': MULT_PRIORITY,
    '%': MULT_PRIORITY,
       
    '+': ADD_PRIORITY,
    '-': ADD_PRIORITY,

    '<<': SHIFT_PRIORITY,
    '>>': SHIFT_PRIORITY,

    '<': REL_PRIORITY,
    '<=': REL_PRIORITY,
    '>': REL_PRIORITY,
    '>=': REL_PRIORITY,

    '==': EQ_PRIORITY,
    '!=': EQ_PRIORITY,

    '&': AND_PRIORITY,
    '^': XOR_PRIORITY,
    '|': OR_PRIORITY,

    '&&': LAND_PRIORITY,
    '||': LOR_PRIORITY
}

