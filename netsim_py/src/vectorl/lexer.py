# ----------------------------------------------------------------------
# clex.py
#
# A lexer for ANSI C.
# ----------------------------------------------------------------------


import ply.lex as lex

# Reserved words
reserved = (
    # types
    'INT', 'REAL', 'BOOL', 'TIME',
    # boolean constants
    'TRUE', 'FALSE',
    # declarations
    'CONST', 'VAR', 'LET', 'EVENT', 'ON', 'FUNC',
    # directives
    'EMIT', 'AFTER',
    # modules
    'IMPORT', 'FROM',
    # control flow
    'IF', 'THEN', 'ELSE'
    )

tokens = reserved + (
    # Literals (identifier, integer constant, float constant, string constant, char const)
    'ID', 'ICONST', 'FCONST', 

    # Operators (+,-,*,/,%,|,&,~,^,<<,>>, ||, &&, !, <, <=, >, >=, ==, !=)
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'OR', 'AND',  'XOR', 'LSHIFT', 'RSHIFT',
    # 'LOR', 'LAND', 'NOT',
    'LNOT',
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
    
    # Assignment (=, :=)
    'EQUALS', 'ASSIGN',

    # Conditional operator (?)
    'CONDOP',
    
    # Delimeters ( ) [ ] { } , . ; :
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'PERIOD', 'SEMI', 'COLON',

    # Ellipsis (...)  _
    'ELLIPSIS',  'SUB'
    )

# Completely ignored characters
t_ignore           = ' \t\x0c'

# Newlines
def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
# Operators
t_PLUS             = r'\+'
t_MINUS            = r'-'
t_TIMES            = r'\*'
t_DIVIDE           = r'/'
t_MOD              = r'%'
t_OR               = r'\|'
t_AND              = r'&'
#t_NOT              = r'~'
t_XOR              = r'\^'
t_LSHIFT           = r'<<'
t_RSHIFT           = r'>>'
#t_LOR              = r'\|\|'
#t_LAND             = r'&&'
t_LNOT             = r'!'
t_LT               = r'<'
t_GT               = r'>'
t_LE               = r'<='
t_GE               = r'>='
t_EQ               = r'=='
t_NE               = r'!='

t_SUB              = r'_'

# Assignment operators

t_EQUALS           = r'='
t_ASSIGN           = r':='


# ?
t_CONDOP           = r'\?'

# Delimeters
t_LPAREN           = r'\('
t_RPAREN           = r'\)'
t_LBRACKET         = r'\['
t_RBRACKET         = r'\]'
t_LBRACE           = r'\{'
t_RBRACE           = r'\}'
t_COMMA            = r','
t_PERIOD           = r'\.'
t_SEMI             = r';'
t_COLON            = r':'
t_ELLIPSIS         = r'\.\.\.'

# Identifiers and reserved words

reserved_map = { }
for r in reserved:
    reserved_map[r.lower()] = r

def t_ID(t):
    r'[A-Za-z_][\w_]*'
    t.type = reserved_map.get(t.value,"ID")
    return t

# Integer literal
t_ICONST = r'\d+'

# Floating literal
t_FCONST = r'((\d+)(\.\d+)(e(\+|-)?(\d+))? | (\d+)e(\+|-)?(\d+))'

# Comments
def t_comment(t):
    r'(/\*(.|\n)*?\*/)|(//.*\n)'
    t.lexer.lineno += t.value.count('\n')

    
def t_error(t):
    #print("Illegal character %s" % repr(t.value[0]))
    #t.lexer.skip(1)
    raise ValueError("Illegal character %s" % repr(t.value[0]))

def get_lexer():
    return lex.lex()

lexer = get_lexer()

if __name__ == "__main__":
    lex.runmain(lexer)

