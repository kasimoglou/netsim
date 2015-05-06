
import pytest
from vectorl.lexer import lexer


@pytest.fixture(params=[
"""
/* This is a nice comment */
""",
"""\
# What a weird comment
# another weird comment
		""",
"",
"""# 
""",
"/**/",
"  \t \n\n\n",
"""
# empty line follows

/*



*/	

/***************************
 ***********************//**/
		"""
])
def empty_lexer(request):
	return request.param

def test_empty_lexer(empty_lexer):
	lexer.input(empty_lexer)
	assert lexer.token() is None

@pytest.fixture(params=[
('x', 'ID'),
('_', 'ID'),
('_131','ID'),
('0', 'ICONST'),
('0312', 'ICONST'),
('572937979798798211239127129', 'ICONST'),
('00121.0','FCONST'),
('0.0','FCONST'),
('0.0e1','FCONST'),
('0.1234634e1','FCONST'),
('1.0e-1','FCONST'),
('1.0e+1','FCONST'),
('1.0e0','FCONST'),
('1.0e00','FCONST'),
('0.0000e1','FCONST')
	])
def single_token(request):
	return request.param

def test_single_tokens(single_token):
	input, tt = single_token
	lexer.input(input)
	# read single token
	token = lexer.token() 
	assert lexer.token() is None
	# check
	assert token.type == tt
	if tt=='ICONST':
		int(token.value)
	elif tt=='FCONST':
		float(token.value)

@pytest.fixture(params=[
 '@', '\\', '$', '#'
])
def error_token(request):
	return request.param

def test_error_token(error_token):
	lexer.input(error_token)
	with pytest.raises(ValueError):
		lexer.token()

	


