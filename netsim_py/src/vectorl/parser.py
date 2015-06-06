

import ply.yacc as yacc
from models.mf import model, attr
from ast import literal_eval
from models.validation import fail, snafu

from vectorl.base import AstNode
from vectorl.lexer import tokens, get_lexer

#
# Parser for vectorl
#

# error handling 
def comperr(p, line, msg, *args, **kwargs):
    lexerr(p.lexer, line, msg, *args, **kwargs)

def lexerr(lex, line, msg, *args, **kwargs):
    name = lex.modelname
    errmsg = msg.format(*args, **kwargs)
    snafu("{0}({1}): error: {2}".format(name, line, errmsg))


def post_advice(p):
    if (not isinstance(p[0], AstNode)) and isinstance(p[0], tuple) and len(p[0])>0 and p[0][0] in {
        'literal', 'array', 'id', 'concat', 'fcall', 'cast',
        'index', 'cond', 'unary', 'binary',
        'block', 'assign', 'emit', 'print', 'if', 
        'import', 'from', 'event', 'func',
            'fexpr', 'const', 'var', 'action',
            'param'
    }:
        p[0] = AstNode(p[0])
        p[0].model_name = p.lexer.modelname
        p[0].lineno = p.lineno(0)
        p[0].linespan = p.linespan(0)





# Rules
def p_error(p):
    if p:
        comperr(p, p.lineno, "Syntax error near {0} token '{1}'", p.type, p.value)
    else:
        fail("Error at end of source")

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
    post_advice(p)

def p_import_as(p):
    'import_clause : IMPORT ID EQUALS ID SEMI'
    p[0] = ('import', p[4], p[2], p.lineno(1))
    post_advice(p)


def p_from_import(p):
    'from_clause : FROM ID IMPORT idlist SEMI'
    p[0] = ('from', p[2], p[4], p.lineno(1))
    post_advice(p)

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
    p[0] = ('param', p[1], p[2])
    post_advice(p)

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
    post_advice(p)


# functions

def p_func_decl(p):
    "func_decl : DEF typename ID LPAREN arglist RPAREN body "
    p[0] = ('func', p[3], p[2], p[5], p[7], p.lineno(1) )
    post_advice(p)


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
    post_advice(p)

def p_cexpr_decl(p):
    """ fexpr_decl : CONST typename ID EQUALS expression SEMI """
    p[0] = ('const', p[3],p[2],p[5])
    post_advice(p)

# variables

def p_var_decl(p):
    """ var_decl : VAR typename ID EQUALS expression SEMI """
    p[0] = ('var', p[3], p[2], p[5])
    post_advice(p)



# actions
def p_event_action(p):
    """ action_decl : ON qual_id statement """
    p[0] = ('action', p[2], p[3])
    post_advice(p)

#
# statements (allowed in actions)
#

def p_block_statement(p):
    """ statement : LBRACE statements RBRACE """
    p[0] = ('block', p[2])
    post_advice(p)

def p_statements_opt(p):
    " statements : "
    p[0] = []

def p_statements(p):
    "statements : statements statement"
    p[0] = p[1] + [p[2]]

def p_emit_statement(p):
    " statement : EMIT qual_id LPAREN expr_list_opt RPAREN AFTER expression SEMI "
    p[0] = ('emit', p[2],p[4],p[7])
    post_advice(p)

def p_assignment(p):
    " statement : concat_expression ASSIGN concat_expression SEMI "
    p[0] = ('assign', p[1], p[3])
    post_advice(p)

def p_fexpr_statement(p):
    " statement : fexpr_decl "
    p[0] = p[1]


#  PRINT


def p_print_statement(p):
    " statement : PRINT LPAREN print_args_opt RPAREN SEMI"
    p[0] = ('print', p[3])
    post_advice(p)

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
    val = p[1]
    if isinstance(val, str):
        val = literal_eval(val)
    p[0] = val

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
    post_advice(p)


#
# Expression grammar
#

def p_primary_expression_literal_int(p):
    " primary_expression : ICONST "
    p[0] = ('literal', int(p[1]))
    post_advice(p)

def p_primary_expression_literal_float(p):
    " primary_expression : FCONST "
    p[0] = ('literal', float(p[1]))
    post_advice(p)

def p_primary_expression_literal_bool(p):
    """ primary_expression : TRUE 
                           | FALSE  """
    p[0] = ('literal', p[1]=='true') 
    post_advice(p)

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
    post_advice(p)

def p_primary_expression_paren(p):
    """ primary_expression :  LPAREN concat_expression RPAREN  """
    p[0] =  p[2]

def p_primary_expression_array(p):
    """ primary_expression : LBRACKET expr_list RBRACKET """
    p[0] = ('array', p[2])
    post_advice(p)

def p_primary_expression_fcall(p):
    """ primary_expression : qual_id LPAREN expr_list_opt RPAREN """
    p[0] = ('fcall', p[1], p[3])
    post_advice(p)

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
    post_advice(p)

def p_index_spec(p):
    """ index_spec : index_seq 
                   | index_seq COMMA ELLIPSIS 
                   | ELLIPSIS 
                   | ELLIPSIS COMMA index_seq 
                   | index_seq COMMA ELLIPSIS COMMA index_seq """
    assert len(p) in (2,4, 6)
    if len(p)==2:
        if p[1]=='ELLIPSIS':
            p[0] = (...,)
        else:
            p[0] = p[1]
    elif len(p)==4:
        if p[1]=='ELLIPSIS':
            p[0] = (...,)+p[3]
        else:
            p[0] = p[1]+(...,)
    else:
        p[0] = p[1]+(...,)+p[5]

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

def p_index_op_range_step(p):
    " index_op : expr_opt COLON expr_opt COLON expr_opt"
    p[0] = slice(p[1],p[3], p[5])

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
    post_advice(p)

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
    post_advice(p)

def p_mult_expression(p):
    """ mult_expression : cast_expression 
                    | mult_expression mult_op cast_expression """ 
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])
    post_advice(p)


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
    post_advice(p)

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
    post_advice(p)

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
    post_advice(p)

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
    post_advice(p)

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
    post_advice(p)

def p_xor_expression(p):
    """ xor_expression : and_expression 
                    | xor_expression XOR and_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])
    post_advice(p)

def p_or_expression(p):
    """ or_expression : xor_expression 
                    | or_expression OR xor_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])
    post_advice(p)

def p_land_expression(p):
    """ land_expression : or_expression 
                    | land_expression LAND or_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])
    post_advice(p)

def p_lor_expression(p):
    """ lor_expression : land_expression 
                    | lor_expression LOR land_expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('binary', p[2], p[1], p[3])
    post_advice(p)


def p_expression(p):
    """ expression : lor_expression 
                    | lor_expression CONDOP expression COLON expression """
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = ('cond', p[1], p[3], p[5])
    post_advice(p)

def p_concat_expression(p):
    """ concat_expression : expression
                          | concat_expression COMMA expression
    """
    if len(p)==2:
        p[0] = p[1]
    else:
        if isinstance(p[1], tuple) and p[1][0]=='concat':
            p[1].append(p[3])
            p[0] = p[1]
        else:
            p[0] = ('concat', [p[1], p[3]])
    post_advice(p)


parser = yacc.yacc()

if __name__=='__main__':
    lexer = get_lexer()
    lexer.modelname = 'example'
    with open('example.vl') as f:
        src = f.read()
    ast = parser.parse(input=src, lexer = lexer, tracking=True)

    print(ast)
